set(openssl_FOUND 1)

if(NOT (TARGET openssl))
	add_library(openssl INTERFACE IMPORTED GLOBAL)
	set_target_properties(openssl PROPERTIES INTERFACE_LINK_LIBRARIES CONAN_PKG::openssl)
endif()

set(openssl_LIBRARIES openssl)
