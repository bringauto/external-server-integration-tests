#include <fleet_protocol/common_headers/device_management.h>
#include <fleet_protocol/common_headers/general_error_codes.h>

#include <test_module.hpp>

int get_module_number() {return MODULE_NUMBER;}

int is_device_type_supported(unsigned int device_type) {
	if(device_type == BUTTON_DEVICE_TYPE) {
		return OK;
	}
	return NOT_OK;
}