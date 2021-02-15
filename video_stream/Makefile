.PHONY = all clean
CC = gcc
GSTREAMER_FLAGS = `pkg-config --cflags --libs gstreamer-1.0`

SRCS := $(wildcard *.c)
BINS := $(SRCS:%.c=%)

all: ${BINS}

src: udp_stream

rec: udp_receive

%: %.c
	${CC} ${GSTREAMER_FLAGS} $< -o $@

clean:
	rm ${BINS}

