PYTHON ?= python3
CXX ?= g++
CXXFLAGS ?= -O3 -std=c++17 -Wall -Wextra -pedantic

.PHONY: all build-graph cnf verify verify-legacy check-g65 test

all: verify

build-graph:
	$(PYTHON) scripts/build_graph.py

cnf:
	$(PYTHON) scripts/generate_cnf.py

verify: build-graph cnf
	$(PYTHON) scripts/verify.py

verify-legacy:
	$(PYTHON) scripts/verify_legacy.py

build/color: scripts/color.cpp
	mkdir -p build
	$(CXX) $(CXXFLAGS) $< -o $@

check-g65: build/color
	$(PYTHON) scripts/check_g65.py

test:
	$(PYTHON) -m unittest discover -s tests -v
