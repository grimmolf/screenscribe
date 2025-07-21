# Screenscribe Fabric Extension
# 
# This project is now implemented as a Go-based Fabric extension.
# The main implementation is in the fabric-extension/ directory.

.PHONY: build install clean test help

# Forward all commands to the fabric-extension directory
help:
	@echo "Screenscribe Fabric Extension"
	@echo "Main implementation is in fabric-extension/ directory"
	@echo ""
	@cd fabric-extension && $(MAKE) help

build:
	@cd fabric-extension && $(MAKE) build

install:
	@cd fabric-extension && $(MAKE) install
	./scripts/install_ffmpeg.sh

test:
	@cd fabric-extension && $(MAKE) test

clean:
	@cd fabric-extension && $(MAKE) clean
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete

deps:
	@cd fabric-extension && $(MAKE) deps

dev: clean build test