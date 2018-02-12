import time

import inject


address = 0x5B4098

with inject.Process(name='AssaCrip_en.exe') as process:
    try:
        while True:
            process.write_int32(address, 2**31 - 1)
            time.sleep(0.1)
    except KeyboardInterrupt:
        process.write_int32(address, 1)
