#include "output.h"
#include "masscan.h"
#include "pixie-sockets.h"
#include "logger.h"
#include <ctype.h>

/****************************************************************************
 * Receive a full line from the socket
 ****************************************************************************/
static size_t
recv_line(SOCKET fd, void *buf, size_t buf_size)
{
    size_t count = 0;

    while (count < buf_size) {
        size_t bytes_received;

        bytes_received = recv(fd, (char*)buf+count, 1, 0);
        if (bytes_received == 0) {
            LOG(0, "redis: recv_line() failed\n");
            exit(1);
        }
        count++;
        if (((unsigned char*)buf)[count-1] == '\n')
            break;
    }

    return count;
}

/****************************************************************************
 ****************************************************************************/
static int
parse_state_machine(struct Output *out, const unsigned char *px, size_t length)
{
    unsigned state = out->redis.state;
    unsigned i;
    enum {
        START,
        NUMBER,
        P,
        PO,
        PON,
        PONG,
        PONG_CR,
        PONG_CR_LF
    };

    for (i=0; i<length; i++)
    switch (state) {
    case START:
        switch (px[i]) {
        case '+':
            state = P;
            break;
        case ':':
            state = NUMBER;
            break;
        default:
            LOG(0, "redis: unexpected data: %.*s\n", length-i, px+i);
            exit(1);
            break;
        }
        break;
    case NUMBER:
        if (isdigit(px[i]) || px[i] == '\r')
            ;
        else if (px[i] == '\n') {
            state = 0;
            if (out->redis.outstanding == 0) {
                LOG(0, "redis: out of sync\n");
                exit(1);
            }
            out->redis.outstanding--;
        } else {
            LOG(0, "redis: unexpected data: %.*s\n", length-i, px+i);
            exit(1);
        }
        break;
    case P:
    case PO:
    case PON:
    case PONG_CR:
    case PONG_CR_LF:
        if ("PONG+\r\n"[i-P] == px[i]) {
            state++;
            if (px[i] == '\n') {
                out->redis.state = 0;
                return 1;
            }
        } else {
            LOG(0, "redis: unexpected data: %.*s\n", length-i, px+i);
            exit(1);
        }
    default:
        LOG(0, "redis: unexpected state: %u\n", state);
        exit(1);
    }
    out->redis.state = state;
    return 0;
}

/****************************************************************************
 ****************************************************************************/
static int
clean_response_queue(struct Output *out, SOCKET fd)
{
    fd_set readfds;
    struct timeval tv = {0,0};
    int x;
    int nfds;
    unsigned char buf[1024];
    size_t bytes_read;

    FD_ZERO(&readfds);
#ifdef _MSC_VER
#pragma warning(disable:4127)
#endif
    FD_SET(fd, &readfds);
    nfds = (int)fd;

    x = select(nfds, &readfds, 0, 0, &tv);
    if (x == 0)
        return 1;
    if (x < 0) {
        LOG(0, "redis:select() failed\n");
        exit(1);
    }
    if (x != 1) {
        LOG(0, "redis:select() failed\n");
        exit(1);
    }

    /*
     * Data exists, so parse it
     */
    bytes_read = recv(fd, (char*)buf, sizeof(buf), 0);
    if (bytes_read == 0) {
        LOG(0, "redis:recv() failed\n");
        exit(1);
    }

    return parse_state_machine(out, buf, bytes_read);
}


/****************************************************************************
 ****************************************************************************/
static void
redis_out_open(struct Output *out, FILE *fp)
{
    ptrdiff_t fd = (ptrdiff_t)fp;
    size_t count;
    unsigned char line[1024];

    UNUSEDPARM(out);

    count = send(fd, "PING\r\n", 6, 0);
    if (count != 6) {
        LOG(0, "redis: send(ping) failed\n");
        exit(1);
    }

    count = recv_line(fd, line, sizeof(line));
    if (count != 7 && memcmp(line, "+PONG\r\n", 7) != 0) {
        LOG(0, "redis: unexpected response from redis server: %s\n", line);
        exit(1);
    }
}

/****************************************************************************
 ****************************************************************************/
static void
redis_out_close(struct Output *out, FILE *fp)
{
    ptrdiff_t fd = (ptrdiff_t)fp;
    size_t count;
    unsigned char line[1024];

    UNUSEDPARM(out);

    count = send(fd, "PING\r\n", 6, 0);
    if (count != 6) {
        LOG(0, "redis: send(ping) failed\n");
        exit(1);
    }

    count = recv_line(fd, line, sizeof(line));
    if (count != 7 && memcmp(line, "+PONG\r\n", 7) != 0) {
        LOG(0, "redis: unexpected response from redis server: %s\n", line);
        exit(1);
    }
}

/****************************************************************************
 ****************************************************************************/
static void
redis_out_status(struct Output *out, FILE *fp, time_t timestamp,
    int status, unsigned ip, unsigned ip_proto, unsigned port, unsigned reason, unsigned ttl)
{
    ptrdiff_t fd = (ptrdiff_t)fp;
    char line[1024];
    char ip_string[16];
    char port_string[10];
    size_t count;
    char values[64];

    sprintf_s(ip_string, sizeof(ip_string), "%u.%u.%u.%u",
        (unsigned char)(ip>>24),
        (unsigned char)(ip>>16),
        (unsigned char)(ip>> 8),
        (unsigned char)(ip>> 0));
    sprintf_s(port_string, sizeof(port_string), "%u/%s", port, name_from_ip_proto(ip_proto));

/**3
$3
SET
$5
mykey
$7
myvalue
*/

    /*
     * KEY: "host"
     * VALUE: ip
     */
    sprintf_s(line, sizeof(line),
            "*3\r\n"
            "$4\r\nSADD\r\n"
            "$%u\r\n%s\r\n"
            "$%u\r\n%s\r\n"
            ,
            (unsigned)strlen("host"), "host",
            (unsigned)strlen(ip_string), ip_string
            );

    count = send(fd, line, (int)strlen(line), 0);
    if (count != strlen(line)) {
        LOG(0, "redis: error sending data\n");
        exit(1);
    }
    out->redis.outstanding++;

    /*
     * KEY: ip
     * VALUE: port
     */
    sprintf_s(line, sizeof(line),
            "*3\r\n"
            "$4\r\nSADD\r\n"
            "$%u\r\n%s\r\n"
            "$%u\r\n%s\r\n"
            ,
            (unsigned)strlen(ip_string), ip_string,
            (unsigned)strlen(port_string), port_string);

    count = send(fd, line, (int)strlen(line), 0);
    if (count != strlen(line)) {
        LOG(0, "redis: error sending data\n");
        exit(1);
    }
    out->redis.outstanding++;


    /*
     * KEY: ip:port
     * VALUE: timestamp:status:reason:ttl
     */
    sprintf_s(values, sizeof(values), "%u:%u:%u:%u",
        (unsigned)timestamp, status, reason, ttl);
    sprintf_s(line, sizeof(line),
            "*3\r\n"
            "$4\r\nSADD\r\n"
            "$%u\r\n%s:%s\r\n"
            "$%u\r\n%s\r\n"
            ,
            (unsigned)(strlen(ip_string) + 1 + strlen(port_string)),
            ip_string,port_string,
            (unsigned)strlen(values), values
            );

    count = send(fd, line, (int)strlen(line), 0);
    if (count != strlen(line)) {
        LOG(0, "redis: error sending data\n");
        exit(1);
    }
    out->redis.outstanding++;

    clean_response_queue(out, fd);

}

/****************************************************************************
 ****************************************************************************/
static void
redis_out_banner(struct Output *out, FILE *fp, time_t timestamp,
        unsigned ip, unsigned ip_proto, unsigned port,
        enum ApplicationProtocol proto, unsigned ttl,
        const unsigned char *px, unsigned length)
{
    UNUSEDPARM(ttl);
    UNUSEDPARM(timestamp);
    UNUSEDPARM(out);
    UNUSEDPARM(fp);
    UNUSEDPARM(ip);
    UNUSEDPARM(ip_proto);
    UNUSEDPARM(port);
    UNUSEDPARM(proto);
    UNUSEDPARM(px);
    UNUSEDPARM(length);

}


/****************************************************************************
 ****************************************************************************/
const struct OutputType redis_output = {
    "redis",
    0,
    redis_out_open,
    redis_out_close,
    redis_out_status,
    redis_out_banner
};



