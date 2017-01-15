
CC = ../../../wla_dx_9.5/binaries/wla-z80
CFLAGS = -o
LD = ../../../wla_dx_9.5/binaries/wlalink
LDFLAGS = -vds

SFILES = main.asm
IFILES = init.inc sound.inc
OFILES = main.o

all: $(OFILES) $(OFILES) makefile
	$(LD) $(LDFLAGS) linkfile rom.sms

main.o: main.asm $(IFILES)
	$(CC) $(CFLAGS) main.asm main.o


$(OFILES): $(HFILES)


clean:
	rm -f $(OFILES) core *~ rom.sms linked.sym
