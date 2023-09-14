from conans import ConanFile, CMake, tools
import os


class OpenSSLTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"
    options = {
        "bitcode": [True, False],
        "windows_version": ["ANY"],
        "windows_sdk": ["ANY"],
        "use_tv_linux_toolchain": [True, False],  # True for the Linux client; False for the Linux Router
        "shared": [True, False]
    }
    default_options = {
        "bitcode": False,
        "windows_version": "Windows8",
        "windows_sdk": "10.0",
        "use_tv_linux_toolchain": False,
        "shared": False
    }


    def build(self):
        if self.settings.os == "iOS":
            return
        cmake = CMake(self)
        env = {}
        if self.options.use_tv_linux_toolchain:
            os.environ['CPPFLAGS'] = os.environ['TV_CPPFLAGS']
            os.environ['CFLAGS'] = os.environ['TV_CFLAGS']
            os.environ['CXXFLAGS'] = os.environ['TV_CXXFLAGS']
            os.environ['LDFLAGS'] = os.environ['TV_LDFLAGS']

            env = {
                "CXXFLAGS": [os.environ['CXXFLAGS']],
                "LDFLAGS": [os.environ['LDFLAGS']],
                "CFLAGS": [os.environ['CFLAGS']]
            }
        if self.settings.os == "Android":
            cmake.definitions['ANDROID_ABI'] = tools.to_android_abi(self.settings.arch)
            cmake.definitions['ANDROID_PLATFORM'] = 'android-' + str(self.settings.os.api_level)
            cmake.definitions['ANDROID_STL'] = 'c++_shared'

        with tools.environment_append(env):
            if self.settings.os == "Emscripten":
                self.run('emcmake cmake {0} {1}'.format(cmake.command_line, self.source_folder))
            else:
                cmake.configure()

        cmake.build()


    def imports(self):
        if self.settings.os == "Android" or self.settings.os == "iOS":
            return
        if not self.options.use_tv_linux_toolchain:
            self.copy("*.dll", dst="bin", src="bin")
            self.copy("*.dylib*", dst="bin", src="lib")


    def test(self):
        if (self.settings.os in ["Android", "iOS", "WindowsStore", "Emscripten"]):
            self.output.info('Skipping test run')
            return
        if ("arm" in self.settings.arch):
            self.output.info('Skipping test run')
            return
        if self.settings.os == "Linux":
            if self.settings.arch == "x86_64" or self.settings.arch == "x86":
                os.chdir("bin")
                self.run(".%stest_application" % os.sep)
            else:
                self.output.info('Skipping test run')
        else:
            os.chdir("bin")
            self.run(".%stest_application" % os.sep)
