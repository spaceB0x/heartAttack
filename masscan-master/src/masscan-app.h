#ifndef MASSCAN_APP_H
#define MASSCAN_APP_H

/*
 * WARNING: these constants are used in files, so don't change the values.
 * Add new ones onto the end
 */
enum ApplicationProtocol {
    PROTO_NONE,
    PROTO_HEUR,
    PROTO_SSH1,
    PROTO_SSH2,
    PROTO_HTTP,
    PROTO_FTP1,
    PROTO_FTP2,
    PROTO_DNS_VERSIONBIND,
    PROTO_SNMP,             /* simple network management protocol, udp/161 */
    PROTO_NBTSTAT,          /* netbios, udp/137 */
    PROTO_SSL3,
    PROTO_SMTP,
    PROTO_POP3,
    PROTO_IMAP4,
    PROTO_UDP_ZEROACCESS,
    PROTO_X509_CERT,
    PROTO_HTML_TITLE,
    PROTO_HTML_FULL,
    PROTO_NTP,              /* network time protocol, udp/123 */
    PROTO_VULN,
    PROTO_HEARTBLEED
};

const char *
masscan_app_to_string(enum ApplicationProtocol proto);

enum ApplicationProtocol
masscan_string_to_app(const char *str);

#endif
