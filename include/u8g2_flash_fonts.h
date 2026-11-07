#pragma once

// U8g2 keeps fonts in RAM here, which leaves the ESP8266 almost no heap.
// Put them in flash and read them with pgm_read_byte_near.
// Force-included from platformio.ini, because a -D flag with parentheses
// breaks the build on Linux.
#define U8X8_FONT_SECTION(name) __attribute__((section(".irom.text." name)))
#define u8x8_pgm_read(adr) pgm_read_byte_near(adr)
