# Loads the programme and runs its tests. Tests run against a checkout of
# micropython-reterminal-sticky: its test runner, fakes and simulator, and its unix port (built
# there with `make submodules unix`).
STICKY ?= micropython-reterminal-sticky
IMAGE ?= espressif/idf:v5.5.2
MPREMOTE ?= uv run mpremote
ESPTOOL ?= uv run esptool
WEB_PORT ?= 8000

STICKY_DIR := $(realpath $(STICKY))
# The board sees only the mounted folder, so device tests copy what they need from STICKY here.
STAGE = build/sticky
# Pulses EN, as the Reset button does: mpremote leaves the programme stopped.
RESET = $(ESPTOOL) --port $(PORT) read-mac > /dev/null

.PHONY: load reset test test-device web port sticky

port:
	@test -n "$(PORT)" || { echo "PORT=… must name the Sticky's serial port"; exit 1; }

sticky:
	@test -n "$(STICKY_DIR)" || { echo "STICKY=… must name a checkout of the port"; exit 1; }

load: port
	$(MPREMOTE) connect $(PORT) cp -r device/* :
	$(RESET)

reset: port
	$(RESET)

# The unix port is built for x86-64 (its viper needs it), so it runs in the port's image.
test: sticky
	docker run --rm --platform linux/amd64 -v $(CURDIR):$(CURDIR) -v $(STICKY_DIR):$(STICKY_DIR) \
		-w $(STICKY_DIR) $(IMAGE) build/unix/micropython tests/run.py $(CURDIR)/tests/unix

test-device: port sticky
	rm -rf $(STAGE) && mkdir -p $(STAGE)
	cd $(STICKY_DIR) && rsync -aR tests/run.py lib boards/SEEED_RETERMINAL_STICKY/modules \
		micropython/lib/micropython-lib/python-stdlib/unittest $(CURDIR)/$(STAGE)/
	$(RESET)
	$(MPREMOTE) connect $(PORT) sleep 2 mount . exec "import os, sys; \
		os.chdir('$(STAGE)'); sys.argv[:] = ['run.py', '/remote/tests/device']; \
		exec(open('tests/run.py').read())"; \
		status=$$?; $(RESET); exit $$status

# The test page, opened once the server is up. Web Bluetooth needs Chrome and localhost.
web:
	(sleep 1 && python3 -m webbrowser -t http://localhost:$(WEB_PORT)/web/) & \
		python3 -m http.server $(WEB_PORT) --bind 127.0.0.1
