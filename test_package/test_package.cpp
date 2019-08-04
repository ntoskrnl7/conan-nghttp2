#include <cstdio>

#ifndef _SSIZE_T_DEFINED
#define _SSIZE_T_DEFINED
#undef ssize_t
#ifdef _WIN64
  typedef __int64 ssize_t;
#else
  typedef int ssize_t;
#endif /* _WIN64 */
#endif /* _SSIZE_T_DEFINED */

#include <nghttp2/nghttp2.h>
#include <nghttp2/nghttp2ver.h>

int main()
{
    nghttp2_info* info = nghttp2_version(NGHTTP2_VERSION_NUM);
    if (info) {
        printf("nghttp2 ver=%d version=%s\n", info->version_num, info->version_str);
    } else {
        printf("nghttp2: cannot get version\n");
    }
    return 0;
}

// vim: et ts=4 sw=4
