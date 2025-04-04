CC = gcc
CXX = g++

CFLAGS = -Wall -Wextra -Wpedantic -Werror -std=c11
CXXFLAGS = -Wall -Wextra -Wpedantic -Werror -std=c++17
LDFLAGS = -lstdc++ -lm
TEST_LDFLAGS = -lgtest -lgtest_main -lpthread

SRC_DIR = src
BUILD_DIR = build
UNIT_TESTS_DIR = tests/unit

# Application
APP_SRC = $(SRC_DIR)/main.c $(SRC_DIR)/calculator.c
APP_OBJ = $(BUILD_DIR)/main.o $(BUILD_DIR)/calculator.o
APP_EXE = $(BUILD_DIR)/app.exe

# Unit tests
TEST_SRC = $(UNIT_TESTS_DIR)/tests.cpp $(SRC_DIR)/calculator.c
TEST_OBJ = $(BUILD_DIR)/tests.o $(BUILD_DIR)/calculator.o
TEST_EXE = $(BUILD_DIR)/unit-tests.exe

# GoogleTest files
GTEST_DIR = googletest
GTEST_BUILD = $(GTEST_DIR)/build
GTEST_LIB = $(GTEST_BUILD)/lib/libgtest.a

# Formatting configuration
FORMAT_DIRS = $(SRC_DIR) $(UNIT_TESTS_DIR)
FORMAT_EXTS = *.cpp *.c *.h
CLANG_FORMAT = clang-format

# Python integration tests
VENV = venv
PIP = $(VENV)/bin/pip
INT_TEST_DIR = tests/integration
INT_TESTS = $(INT_TEST_DIR)/tests.py
INT_TESTS_SERVER = $(INT_TEST_DIR)/tests_server.py

# Server
SERVER = calc_server

# Docker
IMAGE_NAME := calculator-sakhovsky-il-web
CONTAINER_NAME := calc_server_container
DOCKER_PORT  := 8000
HOST_PORT    := 8000

.PHONY: all clean run-app run-unit-test format venv run-integration-tests run-server build-docker run-docker stop-docker clean-docker check-server-dependencies check-client-dependencies

all: $(APP_EXE) $(TEST_EXE)

# Build application
$(APP_EXE): $(APP_OBJ)
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

$(BUILD_DIR)/main.o: $(SRC_DIR)/main.c
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -c -o $@ $<

$(BUILD_DIR)/calculator.o: $(SRC_DIR)/calculator.c
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -c -o $@ $<

# GoogleTest download and build
$(GTEST_DIR)/CMakeLists.txt:
	git clone https://github.com/google/googletest.git $(GTEST_DIR)

$(GTEST_LIB): $(GTEST_DIR)/CMakeLists.txt
	mkdir -p $(GTEST_BUILD)
	cd $(GTEST_BUILD) && cmake .. && make

# Build unit tests
$(TEST_EXE): $(TEST_OBJ) $(GTEST_LIB)
	@mkdir -p $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(TEST_LDFLAGS) $(LDFLAGS)

$(BUILD_DIR)/tests.o: $(UNIT_TESTS_DIR)/tests.cpp
	@mkdir -p $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -c -o $@ $<

clean: clean-docker
	rm -rf $(BUILD_DIR)

run-int: $(APP_EXE)
	@$<

run-float: $(APP_EXE)
	@$< --float

run-unit-test: $(TEST_EXE)
	@$<

format:
	@find $(FORMAT_DIRS) -type f \( \
		-name "*.cpp" -o \
		-name "*.c" -o \
		-name "*.h" \
	\) -exec $(CLANG_FORMAT) -i -style=file {} +

$(VENV):
	@python3 -m venv $(VENV)
	@$(PIP) install --upgrade pip
	@$(MAKE) -s check-server-dependencies
	@$(MAKE) -s check-client-dependencies
	@$(MAKE) -s $(VENV)-testing
	@$(PIP) check

$(VENV)-server:
	@python3 -m venv $(VENV)
	@$(PIP) install --upgrade pip
	@$(MAKE) -s check-server-dependencies
	@$(PIP) check

$(VENV)-client:
	@python3 -m venv $(VENV)
	@$(PIP) install --upgrade pip
	@$(MAKE) -s check-client-dependencies
	@$(PIP) check

$(VENV)-testing:
	@python3 -m venv $(VENV)
	@$(PIP) install --upgrade pip
	@if ! $(PIP) show pytest >/dev/null 2>&1; then \
		$(PIP) install pytest; \
	fi
	@$(PIP) check

check-server-dependencies:
	@if ! $(PIP) show django >/dev/null 2>&1; then \
		$(PIP) install django; \
	fi
	@if ! $(PIP) show djangorestframework >/dev/null 2>&1; then \
		$(PIP) install djangorestframework; \
	fi
	@if ! $(PIP) show channels >/dev/null 2>&1; then \
		$(PIP) install channels; \
	fi
	@if ! $(PIP) show daphne >/dev/null 2>&1; then \
		$(PIP) install daphne; \
	fi
	@if ! $(PIP) show channels_redis >/dev/null 2>&1; then \
		$(PIP) install channels_redis; \
	fi
	@$(PIP) check

check-client-dependencies:
	@if ! $(PIP) show PySide6 >/dev/null 2>&1; then \
		$(PIP) install PySide6; \
	fi
	@$(PIP) check

run-integration-tests: $(VENV)-testing $(APP_EXE)
	@. venv/bin/activate && \
	pytest $(INT_TESTS) && \
	pytest $(INT_TESTS_SERVER) && \
	deactivate

run-server-python: $(VENV)-server $(APP_EXE)
	@. venv/bin/activate && \
	python3 CalculatorApp/manage.py migrate && \
	python3 CalculatorApp/manage.py runserver 0.0.0.0:8000 && \
	deactivate

run-server:
	docker compose up --watch

# ensure-docker-image: Dockerfile
# 	@if ! docker image inspect $(IMAGE_NAME) >/dev/null 2>&1; then \
# 		$(MAKE) build-docker; \
# 	else \
# 		echo "Docker image $(IMAGE_NAME) already exists"; \
# 	fi

# build-docker:
# 	@echo "Building Docker image $(IMAGE_NAME)..."
# 	docker build -t $(IMAGE_NAME) .

# run-docker: ensure-docker-image
# 	@echo "Running Docker container $(CONTAINER_NAME)..."
# 	docker run --name $(CONTAINER_NAME) -p $(HOST_PORT):$(DOCKER_PORT) $(IMAGE_NAME)


stop-server:
	@echo "Stopping Docker containers $(CONTAINER_NAME)..."
	docker compose down

clean-docker:
	@echo "Cleaning up Docker images..."
	docker rmi $(IMAGE_NAME)

run-gui: $(VENV)-client
	@. venv/bin/activate && \
	python3 -m client && \
	deactivate