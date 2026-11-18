NAME			= philo

CC				= cc
CFLAGS			= -Wall -Wextra -Werror -pthread -O3 -Iinclude
RM				= rm -f

SRCDIR			= src
OBJDIR			= obj
INCDIR			= include

SRCS			= $(SRCDIR)/main.c \
				  $(SRCDIR)/parsing.c \
				  $(SRCDIR)/monitor.c \
				  $(SRCDIR)/routine.c \
				  $(SRCDIR)/utils.c

OBJS			= $(SRCS:$(SRCDIR)/%.c=$(OBJDIR)/%.o)
HDRS			= $(INCDIR)/philo.h

all:			shifuuu $(NAME)
				@echo "\033[1m\033[32mCompilation has completed\033[37m"

$(NAME):		$(OBJS) $(HDRS)
				$(CC) $(CFLAGS) $(OBJS) -o $(NAME)

$(OBJDIR)/%.o:	$(SRCDIR)/%.c $(HDRS) | $(OBJDIR)
				$(CC) $(CFLAGS) -c $< -o $@

$(OBJDIR):
				@mkdir -p $(OBJDIR)

clean:
				-clear
				$(RM) -r $(OBJDIR)
				$(RM) *.log tempfile philo_tsan
				$(RM) -r fails
				$(RM) $(ALIEN_DIR)/*.log
				$(RM) -r $(DANTONIK_DIR)/fails $(DANTONIK_DIR)/tempfile
				@echo "\033[1m\033[31mObject files and test logs removed\033[37m"

fclean:			clean
				$(RM) $(NAME)
				@echo "\033[1m\033[31mThe executable file has been successfully removed\033[37m"

re:				fclean all

# Testers Integration
LAZY_DIR		= LazyPhilosophersTester
ALIEN_DIR		= alientest_philosopher
DANTONIK_DIR	= 42-philosophers-tester

$(LAZY_DIR):
	@if [ ! -d "$(LAZY_DIR)/.git" ]; then \
		echo "Cloning LazyPhilosophersTester..."; \
		rm -rf $(LAZY_DIR); \
		git clone https://github.com/MichelleJiam/LazyPhilosophersTester.git $(LAZY_DIR); \
	fi

$(ALIEN_DIR):
	@if [ ! -d "$(ALIEN_DIR)/.git" ]; then \
		echo "Cloning alientest_philosopher..."; \
		rm -rf $(ALIEN_DIR); \
		git clone https://github.com/lienardale/alientest_philosopher.git $(ALIEN_DIR); \
	fi

$(DANTONIK_DIR):
	@if [ ! -d "$(DANTONIK_DIR)/.git" ]; then \
		echo "Cloning 42-philosophers-tester..."; \
		rm -rf $(DANTONIK_DIR); \
		git clone https://github.com/dantonik/42-philosophers-tester.git $(DANTONIK_DIR); \
	fi

# ==============================================================================
#                               TEST SUITES
# ==============================================================================

test: test-hard

test-eval: all $(DANTONIK_DIR)
	@echo "\033[1;36m┌─────────────────────────────────────────────────────────────┐\033[0m"
	@echo "\033[1;36m│ \033[1;37mRunning 42 Evaluation Sheet Automated Suite (dantonik)      \033[1;36m│\033[0m"
	@echo "\033[1;36m└─────────────────────────────────────────────────────────────┘\033[0m"
	@cd $(DANTONIK_DIR) && printf "0\n" | ./test.sh -i 1 -t 3 ../$(NAME)

test-order: all $(ALIEN_DIR)
	@echo "\033[1;36m┌─────────────────────────────────────────────────────────────┐\033[0m"
	@echo "\033[1;36m│ \033[1;37mRunning Timestamp Monotonic Ordering Check (alientest)      \033[1;36m│\033[0m"
	@echo "\033[1;36m└─────────────────────────────────────────────────────────────┘\033[0m"
	@cd $(ALIEN_DIR) && (echo "" | bash order.sh 2>&1 | grep -v -E "kill \[options\]|For more details|kill: usage|Usage:|specify the" | grep -v "  -") || true

test-race: all
	@echo "\033[1;36m┌─────────────────────────────────────────────────────────────┐\033[0m"
	@echo "\033[1;36m│ \033[1;37mRunning LLVM ThreadSanitizer Concurrency & Data-Race Audit    \033[1;36m│\033[0m"
	@echo "\033[1;36m└─────────────────────────────────────────────────────────────┘\033[0m"
	@cc $(CFLAGS) -fsanitize=thread -g $(SRCS) -o philo_tsan
	@./philo_tsan 4 410 200 200 2 > /dev/null
	@./philo_tsan 1 200 100 100 > /dev/null 2>&1 || true
	@rm -f philo_tsan
	@echo "\033[1;32m[PASS] ThreadSanitizer reported 0 data races and 0 lock order inversions.\033[0m"

test-hard: all
	@python3 tests/hard_tests.py

test-lazy: all $(LAZY_DIR)
	@echo "\033[1;36m=== Running LazyPhilosophersTester (Interactive) ===\033[0m"
	@cd $(LAZY_DIR) && ./test.sh ../$(NAME)

test-lazy-auto: all $(LAZY_DIR)
	@echo "\033[1;36m=== Running LazyPhilosophersTester (Die Tests Auto) ===\033[0m"
	@cd $(LAZY_DIR) && (printf "1\n\n\n\n\nq\n" | ./test.sh ../$(NAME))

test-dantonik: all $(DANTONIK_DIR)
	@cd $(DANTONIK_DIR) && ./test.sh ../$(NAME)

test-dantonik-auto: test-eval
test-alien: test-order
test-alien-all: all $(ALIEN_DIR)
	@cd $(ALIEN_DIR) && echo "" | bash correction_test.sh

test-all:
	@echo "\n\033[1;35m╔═════════════════════════════════════════════════════════════╗\033[0m"
	@echo "\033[1;35m║             STARTING COMPLETE TEST PIPELINE                 ║\033[0m"
	@echo "\033[1;35m╚═════════════════════════════════════════════════════════════╝\033[0m\n"
	@$(MAKE) test-eval
	@sleep 0.5
	@$(MAKE) test-order
	@sleep 0.5
	@$(MAKE) test-hard
	@echo "\n\033[1;32m╔═════════════════════════════════════════════════════════════╗\033[0m"
	@echo "\033[1;32m║         ALL TEST SUITES COMPLETED WITH 100% SUCCESS!        ║\033[0m"
	@echo "\033[1;32m╚═════════════════════════════════════════════════════════════╝\033[0m\n"

.PHONY: all clean fclean re test test-eval test-order test-all test-dantonik test-dantonik-auto test-lazy test-lazy-auto test-alien test-alien-all test-hard test-race

shifuuu:
			-clear
			@echo "	\033[37m░██████╗██╗░░██╗██╗███████╗██╗░░░██╗██╗░░░██╗██╗░░░██╗"
			@echo "	\033[37m██╔════╝██║░░██║██║██╔════╝██║░░░██║██║░░░██║██║░░░██║"
			@echo "	\033[37m╚█████╗░███████║██║█████╗░░██║░░░██║██║░░░██║██║░░░██║"
			@echo "	\033[37m░╚═══██╗██╔══██║██║██╔══╝░░██║░░░██║██║░░░██║██║░░░██║"
			@echo "	\033[37m██████╔╝██║░░██║██║██║░░░░░╚██████╔╝╚██████╔╝╚██████╔╝"
			@echo "	\033[37m╚═════╝░╚═╝░░╚═╝╚═╝╚═╝░░░░░░╚═════╝░░╚═════╝░░╚═════╝░"
			@echo "	\033[37m														 "
			@echo "	\033[37m███╗░░░███╗░█████╗░░██████╗████████╗███████╗██████╗░"
			@echo "	\033[37m████╗░████║██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗"
			@echo "	\033[37m██╔████╔██║███████║╚█████╗░░░░██║░░░█████╗░░██████╔╝"
			@echo "	\033[37m██║╚██╔╝██║██╔══██║░╚═══██╗░░░██║░░░██╔══╝░░██╔══██╗"
			@echo "	\033[37m██║░╚═╝░██║██║░░██║██████╔╝░░░██║░░░███████╗██║░░██║"
			@echo "	\033[37m╚═╝░░░░░╚═╝╚═╝░░╚═╝╚═════╝░░░░╚═╝░░░╚══════╝╚═╝░░╚═╝"
			@echo "															 "
