# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, AutoToolsBuildEnvironment, tools
import os
import shutil

getotp_h = """
/* Declarations for getopt.
   Copyright (C) 1989-2019 Free Software Foundation, Inc.

   NOTE: The canonical source of this file is maintained with the GNU C Library.
   Bugs can be reported to bug-glibc@gnu.org.

   This program is free software; you can redistribute it and/or modify it
   under the terms of the GNU General Public License as published by the
   Free Software Foundation; either version 2, or (at your option) any
   later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 51 Franklin Street - Fifth Floor, Boston, MA 02110-1301,
   USA.  */

#ifndef _GETOPT_H
#define _GETOPT_H 1

#ifdef	__cplusplus
extern "C" {
#endif

/* For communication from `getopt' to the caller.
   When `getopt' finds an option that takes an argument,
   the argument value is returned here.
   Also, when `ordering' is RETURN_IN_ORDER,
   each non-option ARGV-element is returned here.  */

extern char *optarg;

/* Index in ARGV of the next element to be scanned.
   This is used for communication to and from the caller
   and for communication between successive calls to `getopt'.

   On entry to `getopt', zero means this is the first call; initialize.

   When `getopt' returns -1, this is the index of the first of the
   non-option elements that the caller should itself scan.

   Otherwise, `optind' communicates from one call to the next
   how much of ARGV has been scanned so far.  */

extern int optind;

/* Callers store zero here to inhibit the error message `getopt' prints
   for unrecognized options.  */

extern int opterr;

/* Set to an option character which was unrecognized.  */

extern int optopt;

/* Describe the long-named options requested by the application.
   The LONG_OPTIONS argument to getopt_long or getopt_long_only is a vector
   of `struct option' terminated by an element containing a name which is
   zero.

   The field `has_arg' is:
   no_argument		(or 0) if the option does not take an argument,
   required_argument	(or 1) if the option requires an argument,
   optional_argument 	(or 2) if the option takes an optional argument.

   If the field `flag' is not NULL, it points to a variable that is set
   to the value given in the field `val' when the option is found, but
   left unchanged if the option is not found.

   To have a long-named option do something other than set an `int' to
   a compiled-in constant, such as set a value from `optarg', set the
   option's `flag' field to zero and its `val' field to a nonzero
   value (the equivalent single-letter option character, if there is
   one).  For long options that have a zero `flag' field, `getopt'
   returns the contents of the `val' field.  */

struct option
{
#if defined (__STDC__) && __STDC__
  const char *name;
#else
  char *name;
#endif
  /* has_arg can't be an enum because some compilers complain about
     type mismatches in all the code that assumes it is an int.  */
  int has_arg;
  int *flag;
  int val;
};

/* Names for the values of the `has_arg' field of `struct option'.  */

#define	no_argument		0
#define required_argument	1
#define optional_argument	2

#if defined (__STDC__) && __STDC__
/* HAVE_DECL_* is a three-state macro: undefined, 0 or 1.  If it is
   undefined, we haven't run the autoconf check so provide the
   declaration without arguments.  If it is 0, we checked and failed
   to find the declaration so provide a fully prototyped one.  If it
   is 1, we found it so don't provide any declaration at all.  */
#if !HAVE_DECL_GETOPT
#if defined (__GNU_LIBRARY__) || defined (HAVE_DECL_GETOPT)
/* Many other libraries have conflicting prototypes for getopt, with
   differences in the consts, in unistd.h.  To avoid compilation
   errors, only prototype getopt for the GNU C library.  */
extern int getopt (int argc, char *const *argv, const char *shortopts);
#else
#ifndef __cplusplus
extern int getopt ();
#endif /* __cplusplus */
#endif
#endif /* !HAVE_DECL_GETOPT */

extern int getopt_long (int argc, char *const *argv, const char *shortopts,
		        const struct option *longopts, int *longind);
extern int getopt_long_only (int argc, char *const *argv,
			     const char *shortopts,
		             const struct option *longopts, int *longind);

/* Internal only.  Users should not call this directly.  */
extern int _getopt_internal (int argc, char *const *argv,
			     const char *shortopts,
		             const struct option *longopts, int *longind,
			     int long_only);
#else /* not __STDC__ */
extern int getopt ();
extern int getopt_long ();
extern int getopt_long_only ();

extern int _getopt_internal ();
#endif /* __STDC__ */

#ifdef	__cplusplus
}
#endif

#endif /* getopt.h */"""

define_ssize_t_code = """
#include <sys/types.h>
#ifndef ssize_t
#if !defined(_SYS_TYPES_H_) && !defined(_SYS_TYPES_H)
#define ssize_t int
#endif
#endif
"""

define_msvc_ssize_t_code = """
#include <sys/types.h>
#ifndef _SSIZE_T_DEFINED
#define _SSIZE_T_DEFINED
#undef ssize_t
#ifdef _WIN64
  typedef __int64 ssize_t;
#else
  typedef int ssize_t;
#endif /* _WIN64 */
#endif /* _SSIZE_T_DEFINED */
"""

cmake_msvc_ssize_t = """
  check_type_size("size_t" SIZEOF_SIZE_T)
  if(SIZEOF_SIZE_T EQUAL 4)
	set(ssize_t int)
  else()
	set(ssize_t __int64)
  endif()"""

util_cpp_asn1_ptime_locale_code = """
static const std::locale
    asn1_ptime_locale(std::locale::classic(),
                 new bt::time_input_facet("%b %d %H:%M:%S %Y GMT"));
"""

util_cpp_parse_openssl_asn1_time_print_code = """
#ifdef _WIN32
  // there is no strptime - use boost
  std::stringstream sstr(s.str());
  sstr.imbue(asn1_ptime_locale);
  bt::ptime ltime;
  sstr >> ltime;
  if (!sstr)
    return 0;

  return boost::posix_time::to_time_t(ltime);
#else  // !_WIN32
"""

class Nghttp2Conan(ConanFile):
    name = "nghttp2"
    version = "1.38.0"
    description = "HTTP/2 C Library and tools"
    topics = ("conan", "http")
    url = "https://github.com/bincrafters/conan-nghttp2"
    homepage = "https://nghttp2.org"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "MIT"
    exports = ["LICENSE.md"]
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake", "pkg_config"

    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False],
               "fPIC": [True, False],
               "with_app": [True, False],
               "with_hpack": [True, False],
               "with_asio": [True, False]}
    default_options = {"shared": False,
                       "fPIC": True,
                       "with_app": True,
                       "with_hpack": True,
                       "with_asio": False}

    _source_subfolder = "source_subfolder"

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def requirements(self):
        self.requires.add("zlib/1.2.11@conan/stable")
        if self.options.with_app:
            self.requires.add("OpenSSL/1.0.2r@conan/stable")
            self.requires.add("c-ares/1.15.0@conan/stable")
            self.requires.add("libev/4.25@bincrafters/stable")
            self.requires.add("libxml2/2.9.9@bincrafters/stable")
        if self.options.with_hpack:
            self.requires.add("jansson/2.12@bincrafters/stable")
        if self.options.with_asio:
            # self.requires.add("boost/1.68.0@conan/stable")
            self.requires.add("boost_asio/1.69.0@bincrafters/stable")
            self.requires.add("boost_system/1.69.0@bincrafters/stable")
            self.requires.add("boost_thread/1.69.0@bincrafters/stable")

    def source(self):
        checksum = "8f306995b2805f9f62e9bc042bbf48eb64f6d30b25c04f76cb75d2977d1dd994"
        source_url = "https://github.com/nghttp2/nghttp2"
        tools.get("{0}/releases/download/v{1}/nghttp2-{1}.tar.bz2".format(source_url, self.version), sha256=checksum)
        extracted_folder = "nghttp2-{0}".format(self.version)
        os.rename(extracted_folder, self._source_subfolder)

    def _configure_cmake(self):
        cmake = CMake(self)

        cmake.definitions["ENABLE_SHARED_LIB"] = "ON" if self.options.shared else "OFF"
        cmake.definitions["ENABLE_STATIC_LIB"] = "OFF" if self.options.shared else "ON"
        cmake.definitions["ENABLE_HPACK_TOOLS"] = "ON" if self.options.with_hpack else "OFF"
        cmake.definitions["ENABLE_APP"] = "ON" if self.options.with_app else "OFF"
        cmake.definitions["ENABLE_EXAMPLES"] = "OFF"
        cmake.definitions["ENABLE_PYTHON_BINDINGS"] = "OFF"
        cmake.definitions["ENABLE_FAILMALLOC"] = "OFF"
        # disable unneeded auto-picked dependencies
        cmake.definitions["WITH_LIBXML2"] = "OFF"
        cmake.definitions["WITH_JEMALLOC"] = "OFF"
        cmake.definitions["WITH_SPDYLAY"] = "OFF"

        cmake.definitions["ENABLE_ASIO_LIB"] = "ON" if self.options.with_asio else "OFF"

        if self.options.with_app:
            cmake.definitions['OPENSSL_ROOT_DIR'] = self.deps_cpp_info['OpenSSL'].rootpath
            
        cmake.definitions['ZLIB_ROOT'] = self.deps_cpp_info['zlib'].rootpath

        cmake.definitions["CMAKE_INSTALL_PREFIX"] = self.package_folder
        cmake.definitions["CMAKE_INSTALL_LIBDIR"] = "lib"
        cmake.definitions["CMAKE_INSTALL_BINDIR"] = "bin"
        
        if self.settings.compiler == "Visual Studio":
            tools.replace_in_file(
                'source_subfolder/src/CMakeLists.txt',
                'target_link_libraries(nghttp2_asio',
                'target_link_libraries(nghttp2_asio\n\t\tcrypt32')
                
            tools.replace_in_file(
                'source_subfolder/src/asio_common.cc',
                '#include "asio_common.h"',
                '#include "asio_common.h"\n#include <io.h>')

            tools.replace_in_file(
                'source_subfolder/src/memchunk.h',
                'uint8_t *pos, *last;',
                '#if defined(_MSC_VER) \n  std::_Array_iterator<uint8_t, N> pos;\n  std::_Array_iterator<uint8_t, N> last;\n#else\n  uint8_t *pos, *last;\n#endif')

            tools.save("source_subfolder/getopt.h", getotp_h)
            self.settings.arch
            tools.replace_in_file(
                'source_subfolder/CMakeLists.txt',
                'set(ssize_t int)',
                cmake_msvc_ssize_t)
            
            cmake.definitions["CONAN_CXX_FLAGS"] = "/DNOMINMAX /Zc:__cplusplus"
            cmake.definitions["CONAN_C_FLAGS"] = "/DNOMINMAX /Zc:__cplusplus"
            
            tools.replace_in_file(
                'sources/lib/includes/nghttp2/nghttp2.h',
                '#include <sys/types.h>',
                define_msvc_ssize_t_code)
        # end if self.settings.compiler == "Visual Studio":

        cmake.configure()
        return cmake

    def _build_with_autotools(self):
        if self.options.with_app:
            os.rename('c-ares.pc', 'libcares.pc')
            os.rename('OpenSSL.pc', 'openssl.pc')

        prefix = os.path.abspath(self.package_folder)
        with tools.chdir(self._source_subfolder):
            env_build = AutoToolsBuildEnvironment(self)
            if self.settings.os == 'Windows':
                prefix = tools.unix_path(prefix)
            args = ['--prefix=%s' % prefix]
            if self.options.shared:
                args.extend(['--disable-static', '--enable-shared'])
            else:
                args.extend(['--disable-shared', '--enable-static'])
            if self.options.with_hpack:
                args.append('--enable-hpack-tools')
            else:
                args.append('--disable-hpack-tools')

            if self.options.with_app:
                args.append('--enable-app')
            else:
                args.append('--disable-app')

            args.append('--disable-examples')
            args.append('--disable-python-bindings')
            # disable unneeded auto-picked dependencies
            args.append('--without-jemalloc')
            args.append('--without-systemd')
            args.append('--without-libxml2')

            if self.options.with_asio:
                args.append('--enable-asio-lib')
                args.append('--with-boost=' + self.deps_cpp_info['boost'].rootpath)
            else:
                args.append('--without-boost')

            env_build.configure(args=args)
            env_build.make()
            env_build.make(args=['install'])

    def build(self):
        if self.settings.os == "Windows":
            if self.options.with_asio:
                tools.replace_in_file(
                    'source_subfolder/CMakeLists.txt',
                    'find_package(Boost ',
                    '# find_package(Boost ')
                tools.replace_in_file(
                    'source_subfolder/src/CMakeLists.txt',
                    'target_link_libraries(nghttp2_asio',
                    'target_link_libraries(nghttp2_asio\n\t\tcrypt32\n\t\tws2_32\n\t\tmswsock')
            tools.replace_in_file(
                'source_subfolder/src/util.cc',
                '#include "timegm.h"',
                '#include "timegm.h"\ninline struct tm *gmtime_r(time_t const *timep, struct tm *tmp) { if (gmtime_s(tmp, timep) == 0) return tmp; return 0;}\ninline struct tm *localtime_r(time_t const *timep, struct tm *tmp) { if (localtime_s(tmp, timep) == 0) return tmp; return 0; }')
            tools.replace_in_file(
                'source_subfolder/src/util.cc',
                'new bt::time_input_facet("%a, %d %b %Y %H:%M:%S GMT"));',
                'new bt::time_input_facet("%a, %d %b %Y %H:%M:%S GMT"));' + util_cpp_asn1_ptime_locale_code)
            tools.replace_in_file(
                'source_subfolder/src/util.cc',
                'time_t parse_openssl_asn1_time_print(const StringRef &s) {',
                'time_t parse_openssl_asn1_time_print(const StringRef &s) {' + util_cpp_parse_openssl_asn1_time_print_code)
            tools.replace_in_file(
                'source_subfolder/src/util.cc',
                'return nghttp2_timegm_without_yday(&tm);\n}',
                'return nghttp2_timegm_without_yday(&tm);\n#endif // !_WIN32\n}')
            cmake = self._configure_cmake()
            cmake.build()
        else:
            self._build_with_autotools()

    def package(self):
        self.copy(pattern="COPYING", dst="licenses", src=self._source_subfolder)
        if self.settings.os == "Windows":
            cmake = self._configure_cmake()
            cmake.install()
            cmake.patch_config_paths()

        # remove unneeded directories
        shutil.rmtree(os.path.join(self.package_folder, 'share', 'man'), ignore_errors=True)
        shutil.rmtree(os.path.join(self.package_folder, 'share', 'doc'), ignore_errors=True)

        for la_name in ('libnghttp2.la', 'libnghttp2_asio.la'):
            la_file = os.path.join(self.package_folder, "lib", la_name)
            if os.path.isfile(la_file):
                os.unlink(la_file)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.compiler == 'Visual Studio':
            if not self.options.shared:
                self.cpp_info.defines.append('NGHTTP2_STATICLIB')
