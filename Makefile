SRC = src

VENV = .venv

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
	@uv run python3 -m $(SRC)

venv:
	@echo "⚙️  $(COLOR_LIGHT_GRAY)Creating a virtual environment $(UNDERLINE)using uv$(UNDERLINE_OFF)...$(COLOR_RESET) ⚙️"
	@uv venv $(VENV)
	@echo "✅ $(COLOR_GREEN)Virtual environment '$(VENV)' created!$(COLOR_RESET)"
	@echo "⚠️ $(COLOR_LIGHT_YELLOW) DON'T FORGET TO ACTIVATE IT IF YOU ARE NOT USING UV$(COLOR_RESET)⚠️"

uv-install:
	@echo "⚙️  $(COLOR_LIGHT_GRAY)Installing 'uv' manager...$(COLOR_RESET) ⚙️"
	@curl -LsSf https://astral.sh/uv/install.sh | sh

install:
	@uv sync

debug:
	@uv run python3 -m pdb -m $(SRC)

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
	@uv run python3 -m flake8 $(SRC)
	@echo "🟢 $(COLOR_LIGHT_GREEN)$(UNDERLINE)flake8$(UNDERLINE_OFF) passed!$(COLOR_RESET) 🟢"
	@uv run python3 -m mypy $(SRC) --warn-return-any \
		--warn-unused-ignores --ignore-missing-imports \
		--disallow-untyped-defs --check-untyped-defs
	@echo "🟢 $(COLOR_LIGHT_GREEN)$(UNDERLINE)mypy$(UNDERLINE_OFF) passed!$(COLOR_RESET) 🟢"

lint-strict:
	@uv run python3 -m flake8 $(SRC)
	@echo "🟢 $(COLOR_LIGHT_GREEN)$(UNDERLINE)flake8$(UNDERLINE_OFF) passed!$(COLOR_RESET) 🟢"
	@uv run python3 -m mypy $(SRC) --strict
	@echo "🟢 $(COLOR_LIGHT_GREEN)$(UNDERLINE)mypy$(UNDERLINE_OFF) --strict passed!$(COLOR_RESET) 🟢"

help:
	@echo ""
	@echo "🛠  $(COLOR_GREEN)AVAILABLE COMMANDS$(COLOR_RESET)  🛠"
	@echo ""

	@echo "$(COLOR_LIGHT_YELLOW)run$(COLOR_RESET)\t\tExecutes the src module."
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

.PHONY: install run run_module venv install debug clean lint lint-strict  help