#!/usr/bin/env python
# -*- coding: utf-8 -*
"""Module for nats package."""

import os
from conan import ConanFile
from conan.tools.scm import Git
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import collect_libs
from conan.tools import files

required_conan_version = ">=1.59.0"

class NatsConan(ConanFile):
    name = "nats"
    description = "NATS is a simple, secure and high-performance messaging system."
    version = "3.6.1"
    license = "Apache-2.0"
    settings = "os", "compiler", "build_type", "arch"
    exports_sources = ["patches/*"]
    
    options = {
        "nats_build_streaming"   : [True, False],

        "windows_sdk"            : "ANY",
        "full_compiler_version"  : "ANY"
    }

    default_options = {
        "nats_build_streaming"   : False,

        "windows_sdk"            : "10.0",
        "full_compiler_version"  : ""
    }

    def config_options(self):
        if self.settings.os != "Windows":
            del self.options.windows_sdk

    def layout(self):
        cmake_layout(self, src_folder = "src")

    def generate(self):
        cmake = CMakeDeps(self)
        cmake.generate()
        tc = CMakeToolchain(self)
        tc.variables["NATS_BUILD_STREAMING"] = self.options.nats_build_streaming
        tc.variables["NATS_BUILD_WITH_TLS"] = True
        tc.variables["NATS_BUILD_LIB_STATIC"] = True
        tc.variables["NATS_BUILD_LIB_SHARED"] = False
        tc.variables["NATS_BUILD_EXAMPLES"] = False
        tc.variables["BUILD_TESTING"] = False

        tc.generate()

    def source(self):
        git = Git(self)
        git.clone(url = "https://github.com/nats-io/nats.c.git", target = ".")
        git.checkout("v3.6.1")
        # Apply the patch to the CMekeLists.txt file located in src/
        files.patch(self, patch_file = "patches/nats-src-cmakelists-openssl.patch")

    def requirements(self):
        self.requires("openssl/3.1.1_0@jenkins/stable")
        #self.requires("openssl/3.1.1")
        if self.options.nats_build_streaming:
            self.requires("protobuf/3.18.0_13@jenkins/stable")

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = collect_libs(self)