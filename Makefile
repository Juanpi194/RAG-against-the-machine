SRC = src

ENTRY_POINT = pac-man.py
CONFIG_FILE = config.jsonc
VENV = .venv

REQUIREMENTS_FILE = requirements.txt

COLOR_RESET			:= \033[0m
COLOR_GRAY			:= \033[0;30m
COLOR_LIGHT_GRAY	:= \033[1;30m
COLOR_RED			:= \033[0;31m
COLOR_GREEN			:= \033[0;32m
COLOR_LIGHT_GREEN	:= \033[1;32m
COLOR_YELLOW		:= \033[0;33m
COLOR_LIGHT_YELLOW	:= \033[1;33m
COLOR_BLUE			:= \033[0;34m
COLOR_LIGHT_BLUE	:= \033[1;34m
COLOR_MAGENTA		:= \033[0;35m
COLOR_CYAN			:= \033[0;36m
COLOR_WHITE			:= \033[0;37m
BOLD				:= \033[1m
BOLD_OFF			:= \033[22m
UNDERLINE			:= \033[4m
UNDERLINE_OFF       := \033[24m


run:
	# TODO
	uv run python3 $(ENTRY_POINT) $(CONFIG_FILE)

run_module:
	# TODO
	@python3 -m $(SRC)

venv:
	@echo "⚙️  $(COLOR_LIGHT_GRAY)Creating a virtual environment $(UNDERLINE)using uv$(UNDERLINE_OFF)...$(COLOR_RESET) ⚙️"
	@uv venv $(VENV)
	@echo "✅ $(COLOR_GREEN)Virtual environment '$(VENV)' created!$(COLOR_RESET)"
	@echo "⚠️ $(COLOR_LIGHT_YELLOW) DON'T FORGET TO ACTIVATE IT IF YOU ARE NOT USING UV$(COLOR_RESET)⚠️"

uv-install:
	@echo "⚙️  $(COLOR_LIGHT_GRAY)Installing 'uv' manager...$(COLOR_RESET) ⚙️"
	@curl -LsSf https://astral.sh/uv/install.sh | sh

install:
	@echo "$(COLOR_RED) THIS IS ONLY NEEDED IF YOU ARE NOT USING $(UNDERLINE)UV$(UNDERLINE_OFF)$(COLOR_RESET)"
	@echo "⚠️  $(COLOR_YELLOW)Make sure you are in a $(UNDERLINE)virtual environment$(UNDERLINE_OFF) \
	before installing the dependencies!$(COLOR_RESET) ⚠️"

	@read -p "Are you in the virtual environment? (yes/no) " answer; \
	if [ -z "$$answer" ]; then \
		echo "⛔ Answer was not provided. ⛔"; \
		echo "$(COLOR_RED)Aborting...$(COLOR_RESET)"; \
		exit 1; \
	fi; \
	if [ "$$answer" = "no" ]; then \
		echo "📦 Make sure to be in the virtual environment before installing the packages. 📦"; \
		echo "$(COLOR_LIGHT_GREEN)Use the rule $(COLOR_YELLOW)venv$(COLOR_LIGHT_GREEN) to create it."; \
		echo "$(COLOR_RED)Aborting...$(COLOR_RESET)"; \
		exit 1; \
	fi; \
	if [ ! "$$answer" = "yes" ]; then \
		echo "🚩🚩🚩 Answer provided is not correct. 🚩🚩🚩"; \
		echo "$(COLOR_RED)Aborting...$(COLOR_RESET)"; \
		exit 1; \
	fi;
	@echo "⚒$(COLOR_GRAY) Installing required packages... $(COLOR_RESET)⚒"
	@if [ -f "$(REQUIREMENTS_FILE)" ]; then \
		pip install -r $(REQUIREMENTS_FILE); \
		echo "✅ $(COLOR_GREEN)Installation was successful!$(COLOR_RESET)"; \
	else \
		echo "$(REQUIREMENTS_FILE) is missing!"; \
		echo "❌ $(COLOR_RED)Installation failed$(COLOR_RESET)"; \
	fi

debug:
	@python3 -m pdb $(ENTRY_POINT)

clean:
	@echo "🧹 $(COLOR_GRAY)Cleaning __pycache__ and .mypy_cache directories...$(COLOR_RESET) 🧹"
	@for dir in $(shell find . -type d -name __pycache__); do \
		rm -rf $$dir; \
	done
	@for dir in $(shell find . -type d -name .mypy_cache); do \
		rm -rf $$dir; \
	done
	@echo "⭐ $(COLOR_LIGHT_GREEN)Cleanup was successful$(COLOR_RESET) ⭐"

lint:
	@python3 -m flake8 $(ENTRY_POINT) $(SRC)
	@echo "🟢 $(COLOR_LIGHT_GREEN)$(UNDERLINE)flake8$(UNDERLINE_OFF) passed!$(COLOR_RESET) 🟢"
	@python3 -m mypy $(ENTRY_POINT) $(SRC) --warn-return-any \
		--warn-unused-ignores --ignore-missing-imports \
		--disallow-untyped-defs --check-untyped-defs
	@echo "🟢 $(COLOR_LIGHT_GREEN)$(UNDERLINE)mypy$(UNDERLINE_OFF) passed!$(COLOR_RESET) 🟢"

lint-strict:
	@python3 -m flake8 $(ENTRY_POINT) $(SRC)
	@echo "🟢 $(COLOR_LIGHT_GREEN)$(UNDERLINE)flake8$(UNDERLINE_OFF) passed!$(COLOR_RESET) 🟢"
	@mypy $(ENTRY_POINT) $(SRC) --strict
	@echo "🟢 $(COLOR_LIGHT_GREEN)$(UNDERLINE)mypy$(UNDERLINE_OFF) --strict passed!$(COLOR_RESET) 🟢"

build windows:
	@echo "⚙️  $(COLOR_LIGHT_GRAY)Building executable for Windows...$(COLOR_RESET) ⚙️"
	@uv run python build/build.py --target windows
	@echo "✅ $(COLOR_GREEN)Build finished! Executable: 'dist_windows/Pacman/Pacman.exe'$(COLOR_RESET)"

build linux:
	@echo "⚙️  $(COLOR_LIGHT_GRAY)Building executable for Linux...$(COLOR_RESET) ⚙️"
	@uv run python build/build.py --target linux
	@echo "✅ $(COLOR_GREEN)Build finished! Executable: 'dist_linux/Pacman/Pacman'$(COLOR_RESET)"

help:
	@echo ""
	@echo "🛠  $(COLOR_GREEN)AVAILABLE COMMANDS$(COLOR_RESET)  🛠"
	@echo ""

	@echo "$(COLOR_LIGHT_YELLOW)run$(COLOR_RESET)\t\tExecutes the main.py."
	@echo ""
	
	@echo "$(COLOR_LIGHT_YELLOW)run_module$(COLOR_RESET)\tExecutes the src folder as a module."
	@echo ""
	
	@echo "$(COLOR_LIGHT_YELLOW)venv$(COLOR_RESET)\t\tCreates a virtual environment called '$(VENV)' (Done by uv)."
	@echo ""
	
	@echo "$(COLOR_LIGHT_YELLOW)uv-install$(COLOR_RESET)\tInstalls the $(UNDERLINE)uv manager$(UNDERLINE_OFF)."
	@echo ""

	@echo "$(COLOR_LIGHT_YELLOW)install$(COLOR_RESET)\t\tInstalls all the dependencies needed to run the program."
	@echo ""
	
	@echo "$(COLOR_LIGHT_YELLOW)debug$(COLOR_RESET)\t\tUses the python debugger for the program."
	@echo ""
	
	@echo "$(COLOR_LIGHT_YELLOW)clean$(COLOR_RESET)\t\tRemoves all temporary folders and files from the proyect."
	@echo ""
	
	@echo "$(COLOR_LIGHT_YELLOW)lint$(COLOR_RESET)\t\tRuns the flake8 and mypy modules with all flags required."
	@echo ""
	
	@echo "$(COLOR_LIGHT_YELLOW)lint-strict$(COLOR_RESET)\tRuns the flake8 and mypy modules with the strict flag."
	@echo ""

.PHONY: install run run_module venv install debug clean lint lint-strict "build windows" "build linux" help