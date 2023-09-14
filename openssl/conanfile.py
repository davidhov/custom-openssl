from conans import tools, AutoToolsBuildEnvironment
from conan import ConanFile
from conan.tools import files, microsoft
import os

class OpensslConan(ConanFile):
    homepage = "https://www.openssl.org/"
    license = " OpenSSL License"
    description = "TLS/SSL and crypto library"
    name = "openssl"
    version = "3.1.1_0"
    settings = "os", "arch", "compiler", "build_type"
    exports_sources = ["cmake/*"]
    exports = ["patches/*"]
    options = {
        "shared"                 : [True, False],
        "use_tv_linux_toolchain" : [True, False],
        "visibility"             : ['default', 'hidden'],
        "windows_sdk"            : ["ANY"],
        "win32_winnt"            : ["ANY"],
        "full_compiler_version"  : ["ANY"]
    }
    default_options = {
        "shared"                 : False,
        "use_tv_linux_toolchain" : False,
        "visibility"             : "hidden",
        "windows_sdk"            : "10.0",
        "win32_winnt"            : "0x0000",
        "full_compiler_version"  : ""
    }
    source_dir = "src"
    short_paths = True


    def configure(self):
        if self.settings.os == 'Android':
            if self.settings.compiler != 'clang' or self.settings.compiler.libcxx != 'libc++':
                raise ConanInvalidConfiguration("Since NDK r20 only clang and libc++ are supported")


    def config_options(self):
        if self.settings.os != "Linux":
            del self.options.use_tv_linux_toolchain

        if self.settings.os not in ["Windows", "WindowsStore"]:
            del self.options.windows_sdk

        if self.settings.os == "iOS":
            del self.settings.arch

    def build_requirements(self):
        if microsoft.is_msvc(self):
            if not self.settings.os == "WindowsStore":
                self.build_requires("nasm/2.15.05_1@jenkins/stable")
            self.build_requires("strawberryperl/5.32.1.1_2@jenkins/stable")

        if tools.os_info.is_macos:
            installer = tools.SystemPackageTool()
            installer.install("git-lfs")
            self.run("git lfs install --skip-smudge --skip-repo")
        elif tools.os_info.is_freebsd:
            installer = tools.SystemPackageTool()
            installer.install("gmake")
            installer.install("git-lfs")
            self.run("git lfs install --skip-smudge --skip-repo")


    def source(self):
        self.output.info("downloading source ...")
        upstream_version = self.version.split('_')[0]
        git_dir = "git"
        git = tools.Git(folder = git_dir)
        archive_name = "openssl-%s" % upstream_version
        full_file_name = "%s.tar.gz" % archive_name
        git.run("lfs clone -I %s -b %s --depth 1 ssh://git@bitbucket/lib/openssl.git ." % (full_file_name, upstream_version))
        files.unzip(self, "%s/%s" % (git_dir, full_file_name))
        tools.rmdir(git_dir)
        files.rename(self, archive_name, self.source_dir)


    def configArgsIOS(self):
        configArgs = [
            "no-buildtest-c++",
            "no-external-tests",
            "no-unit-test",
            "no-tests",
            "no-zlib",
            "no-comp",
            "no-hw",
            "no-dso",
            "no-err",
            "no-idea",
            "no-dtls",
            "no-srp",
            "no-ec",
            "no-gost",
            "no-asm",
            "threads",
            "no-rc5",
            "no-engine",
            "no-deprecated"
        ]
        if self.options.shared:
            configArgs.append("shared")
        else:
            configArgs.append("no-shared")

        return configArgs


    def build(self):
        if self.settings.os == "iOS":
            self.output.info("Building iOS lib")
            self.__build_darwin()

        else:
            # set up environment variables
            if self.settings.os == "Linux" and self.options.use_tv_linux_toolchain:
                env = { }
                env['CFLAGS'] = str(os.environ['TV_CFLAGSnoM'])
            elif microsoft.is_msvc(self):
                env = tools.vcvars_dict(self.settings, winsdk_version = str(self.options.windows_sdk))
            else:
                env_build = AutoToolsBuildEnvironment(self)
                env = env_build.vars

            # "config" is for building for the host machine, while "Configure [triplet]" is for cross-building
            if microsoft.is_msvc(self):
                config_command = "perl Configure %s -D_WIN32_WINNT=%s" % (self.__generate_vs_target(), self.options.win32_winnt)
            elif self.settings.os == "Android":
                machine = "android-" + tools.to_android_abi(self.settings.arch).split("-")[0].replace("eabi","")
                config_command = "./Configure " + machine
            elif self.settings.os == "Linux" and self.options.use_tv_linux_toolchain:
                switcher = {
                    "x86": "linux-elf",
                    "x86_64": "linux-x86_64",
                    "armv5el": "linux-armv4",
                    "armv5hf": "linux-armv4",
                    "armv7": "linux-armv4",
                    "armv8": "linux-aarch64",
                }
                machine = switcher.get(str(self.settings.arch), "wrong-architecture")
                config_command = "./Configure " + machine
            else:
                config_command = "./config"

            # name of the system's make program
            if microsoft.is_msvc(self):
                make_program = "nmake"
            elif self.settings.os == "FreeBSD":
                make_program = "gmake"
            else:
                make_program = "make"

            # build only libraries if we cannot run the test suite
            if (self.settings.os in ["Android", "WindowsStore"]) or ((self.settings.os == "Linux") and self.options.use_tv_linux_toolchain):
                run_tests = False
                make_target = " build_libs"
            else:
                run_tests = True
                make_target = ""

            # set up configure arguments
            config_args = "no-srp no-engine no-deprecated --api=1.1.1 --prefix=%s" % self.build_folder
            if self.settings.build_type == 'Release':
                config_args += " --release"
            elif self.settings.build_type == 'Debug':
                config_args += " --debug"
            if self.options.shared:
                config_args += " shared"
            else:
                config_args += " no-shared"
            if self.settings.os == "Android":
                config_args += " -D__ANDROID_API__=" + str(self.settings.os.api_level)
                config_args += " no-buildtest-c++ no-external-tests no-unit-test no-tests no-zlib no-comp no-hw no-dso no-stdio no-err no-idea no-dtls no-ec no-gost no-asm threads no-rc5 -fPIC"
            elif self.settings.os == "Linux" and self.options.use_tv_linux_toolchain:
                config_args += " no-zlib no-zlib-dynamic no-comp no-hw no-dso no-err no-idea no-dtls no-gost "
                config_args += str(os.environ['TV_CFLAGSnoM'])
            elif self.settings.os == "WindowsStore":
                config_args += " enable-capieng no-unit-test no-asm no-uplink no-tests no-secure-memory -utf-8 -FS"

            with files.chdir(self, self.source_dir), tools.environment_append(env):
                self.output.info("configuring...")
                self.run("%s %s" % (config_command, config_args))
                self.output.info("make...")
                self.run(make_program + make_target)
                if run_tests:
                    self.output.info("running tests...")
                    self.run("%s test" % make_program)
                self.output.info("Install lib and headers...")
                if self.settings.os != "WindowsStore":
                    self.run("%s install_sw" % make_program)

            self.output.info("Make paths location independent...")
            for libpath in ["lib", "lib64"]:
                pkgconfig_path = "./%s/pkgconfig" % libpath
                if os.path.isdir(pkgconfig_path):
                    with files.chdir(self, pkgconfig_path):
                        for filename in os.listdir("."):
                            if filename.endswith(".pc"):
                                pkgConfigFile = os.path.abspath(filename)
                                tools.replace_prefix_in_pc_file(pkgConfigFile, "${pcfiledir}/../..")


    def package(self):
        self.copy("*", dst="cmake", src="cmake")
        if self.settings.os == "WindowsStore":
            files.copy(self, "*.h", dst=os.path.join(self.package_folder, "include/openssl"), src="src/include/openssl")
            files.copy(self, "libssl.lib", dst=os.path.join(self.package_folder, "lib"), src="src")
            files.copy(self, "libssl*.dll", dst=os.path.join(self.package_folder, "bin"), src="src")
            files.copy(self, "libcrypto.lib", dst=os.path.join(self.package_folder, "lib"), src="src")
            files.copy(self, "libcrypto*.dll", dst=os.path.join(self.package_folder, "bin"), src="src")
            files.copy(self, "ossl_static.pdb", dst=os.path.join(self.package_folder, "lib"), src="src")
        elif self.settings.os == "iOS":
            # For iOS cURL header files must be generated
            files.copy(self, "*.h", dst=os.path.join(self.package_folder, "include/openssl"), src="output/include/openssl")
            files.copy(self, "libssl.a", dst=os.path.join(self.package_folder, "lib"), src="output/lib")
            files.copy(self, "libcrypto.a", dst=os.path.join(self.package_folder, "lib"), src="output/lib")
        else:
            files.copy(self, "*", dst=os.path.join(self.package_folder, "include"), src="include")
            files.copy(self, "*", dst=os.path.join(self.package_folder, "lib"), src="lib")
            files.copy(self, "*", dst=os.path.join(self.package_folder, "lib"), src="lib64")
            files.copy(self, "*", dst=os.path.join(self.package_folder, "bin"), src="bin")


    def package_info(self):
        self.cpp_info.builddirs = ["cmake"]

        if microsoft.is_msvc(self):
            self.cpp_info.libs = [
                "libssl",
                "libcrypto"
            ]
        else:
            self.cpp_info.libs = [
                "ssl",
                "crypto"
            ]

        if not self.options.shared:
            if self.settings.os in ["Windows", "WindowsStore"]:
                self.cpp_info.system_libs = [
                    "crypt32.lib",
                    "ws2_32.lib"
                ]
            else:
                self.cpp_info.system_libs = [
                    "dl"
                ]
                if self.settings.os == "Linux":
                    if self.options.use_tv_linux_toolchain:
                        self.cpp_info.system_libs += [":libatomic.a"]
                    else:
                        self.cpp_info.system_libs += ["atomic"]
                if self.settings.os == "Android":
                    self.cpp_info.system_libs += ["atomic"]
                else:
                    self.cpp_info.system_libs.append("pthread")

        pkgconfig_path = os.path.join(self.package_folder, "lib/pkgconfig")
        if os.path.isdir(pkgconfig_path):
            self.env_info.PKG_CONFIG_PATH.append(pkgconfig_path)


    def __generate_vs_target(self):
        arch_mapping = {
                "x86" :"VC-WIN32",
                "x86_64" :"VC-WIN64A",
                "armv7" :"VC-WIN32-ARM",
                "armv8" :"VC-WIN64-ARM"
            }
        target = arch_mapping[str(self.settings.arch)]
        if self.settings.build_type == "Debug":
            target = "debug-" + target
        if self.settings.os == "WindowsStore":
            target = target + "-UWP"
        return target


    def __build_darwin(self):
        self.output.info("Build darwin")
        libname_ssl = 'libssl.a'
        libname_crypto = 'libcrypto.a'

        thinlibs_ssl = ''
        thinlibs_crypto = ''
        if self.settings.os == "iOS":
            configArgs = self.configArgsIOS()
            prefixfolder = self.__build_darwin_arch(configArgs, "iphonesimulator", "x86_64", "darwin64-x86_64-cc")
            thinlibs_ssl += ' %s/lib/%s' % (prefixfolder, libname_ssl)
            thinlibs_crypto += ' %s/lib/%s' % (prefixfolder, libname_crypto)

            configArgs = self.configArgsIOS()
            prefixfolder = self.__build_darwin_arch(configArgs, "iphoneos", "arm64", "iphoneos-cross")
            thinlibs_ssl += ' %s/lib/%s' % (prefixfolder, libname_ssl)
            thinlibs_crypto += ' %s/lib/%s' % (prefixfolder, libname_crypto)

        self.run("mkdir output")
        self.run("mkdir output/lib")
        self.run('lipo -create -output "output/lib/%s" %s' % (libname_ssl, thinlibs_ssl))
        self.run('lipo -create -output "output/lib/%s" %s' % (libname_crypto, thinlibs_crypto))
        # copy include folder from latest build - arm64
        self.run('cp -R %s/include output'  % prefixfolder)


    def __build_darwin_arch(self, configArgs, sdk, arch, host):
        self.output.info("Build arch: %s %s " % (arch, sdk))

        prefixfolder = '%s/output_%s' % (self.build_folder, arch)
        configArgs.append("--api=1.1.1")
        configArgs.append("--prefix=%s" % prefixfolder)
        configArgs.append("%s" % host)

        autotools = AutoToolsBuildEnvironment(self)
        env_vars = autotools.vars

        xcrun = tools.XCRun(self.settings, sdk=sdk)
        minOSFlag = tools.apple_deployment_target_flag(self.settings.os, self.settings.os.version)
        env_vars['CC'] = xcrun.cc
        env_vars['CXX'] = xcrun.cxx
        env_vars['CFLAGS'] = "-arch %s -I%s/usr/include -isysroot %s %s" % (arch, xcrun.sdk_path, xcrun.sdk_path, minOSFlag)
        env_vars['LDFLAGS'] = "-arch %s -isysroot %s" % (arch, xcrun.sdk_path)

        if self.options.visibility == 'hidden':
            env_vars['CFLAGS'] += " -fvisibility=hidden"
            env_vars['CFLAGS'] += " -fvisibility-inlines-hidden"

        env_vars['CPPFLAGS'] = env_vars['CFLAGS']

        with files.chdir(self, self.source_dir):
            autotools.configure(args=configArgs, vars=env_vars)
            autotools.make(vars=env_vars)
            autotools.install(vars=env_vars)
            self.run("make clean")

        return prefixfolder
