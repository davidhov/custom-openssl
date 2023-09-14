#include <iostream>
#include <nats/nats.h>

int main()
{
	// Initializing NATS library
    natsStatus status = nats_Open(1);
    if (status == NATS_OK)
    {
        nats_Close();
    }
	std::cout << "NATS library linked properly" << std::endl;
    
    return 0;
}