# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, AutoToolsBuildEnvironment, tools
from conans.errors import ConanInvalidConfiguration
import os
import shutil

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
        if self.options.with_asio and self.settings.compiler == "Visual Studio":
            raise ConanInvalidConfiguration("Build with asio and MSVC is not supported yet, see upstream bug #589")

    def requirements(self):
        self.requires.add("zlib/1.2.11@conan/stable")
        if self.options.with_app:
            self.requires.add("OpenSSL/1.1.1d@conan/stable")
            self.requires.add("c-ares/1.15.0@conan/stable")
            self.requires.add("libev/4.25@bincrafters/stable")
            self.requires.add("libxml2/2.9.9@bincrafters/stable")
        if self.options.with_hpack:
            self.requires.add("jansson/2.12@bincrafters/stable")
        if self.options.with_asio:
            self.requires.add("boost_asio/1.70.0@bincrafters/stable")
            self.requires.add("boost_system/1.70.0@bincrafters/stable")
            self.requires.add("boost_thread/1.70.0@bincrafters/stable")

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
