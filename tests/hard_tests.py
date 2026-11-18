#!/usr/bin/env python3
"""
=============================================================================
42 PHILOSOPHERS - COMPREHENSIVE AUTOMATED TEST SUITE
=============================================================================
Tests concurrency, parsing edge-cases, single-philosopher deadlocks, 
timestamp ordering, starvation avoidance, tight death margins, and data races.
=============================================================================
"""

import subprocess
import time
import sys
import os

# ANSI Color Codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
WHITE = "\033[97m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

PASS_BADGE = f"{GREEN}{BOLD}PASS ✓{RESET}"
FAIL_BADGE = f"{RED}{BOLD}FAIL ✗{RESET}"

PHILO_BIN = os.path.abspath("./philo")
passed_count = 0
failed_count = 0
suite_start_time = 0

def kill_philo():
    subprocess.run(["pkill", "-x", "-9", "philo"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "-x", "-9", "philo_tsan"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def check_timestamps(lines):
    prev_ts = -1
    for line in lines:
        parts = line.strip().split()
        if not parts:
            continue
        if parts[0].isdigit():
            ts = int(parts[0])
            if prev_ts != -1 and ts < prev_ts:
                return False, f"Timestamp out of order: {ts}ms after {prev_ts}ms"
            prev_ts = ts
    return True, ""

def format_row(name, args_str, duration_str, status_badge, detail=""):
    name_col = f"{name:<44}"
    args_col = f"{DIM}{args_str:<22}{RESET}"
    dur_col = f"{DIM}{duration_str:>7}{RESET}"
    line = f"  {name_col} {args_col} {dur_col}  {status_badge}"
    if detail:
        line += f"  {YELLOW}({detail}){RESET}"
    return line

def print_section(title):
    print(f"\n{BOLD}{CYAN}┌─────────────────────────────────────────────────────────────────────────────┐{RESET}")
    print(f"{BOLD}{CYAN}│ {WHITE}{title:<75}{CYAN}│{RESET}")
    print(f"{BOLD}{CYAN}└─────────────────────────────────────────────────────────────────────────────┘{RESET}")

def run_test(name, args, expected_death=None, min_death_ts=None, max_death_ts=None, 
             should_error=False, timeout=10, binary=PHILO_BIN):
    global passed_count, failed_count
    kill_philo()
    
    cmd = [binary] + [str(a) for a in args]
    args_display = " ".join(str(a) for a in args) if args else "(none)"
    if len(args_display) > 20:
        args_display = args_display[:18] + ".."

    t0 = time.time()
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                              text=True, timeout=timeout)
        duration = time.time() - t0
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired:
        kill_philo()
        duration = time.time() - t0
        print(format_row(name, args_display, f"{duration:.2f}s", FAIL_BADGE, f"Timed out after {timeout}s"))
        failed_count += 1
        return False

    lines = [l for l in stdout.splitlines() if l.strip()]
    dur_str = f"{duration:.2f}s"

    # 1. Error handling verification
    if should_error:
        if proc.returncode != 0 or any("error" in l.lower() for l in lines) or any("error" in l.lower() for l in stderr.splitlines()):
            print(format_row(name, args_display, dur_str, PASS_BADGE, "graceful error"))
            passed_count += 1
            return True
        else:
            print(format_row(name, args_display, dur_str, FAIL_BADGE, "expected error, got 0"))
            failed_count += 1
            return False

    # 2. Timestamp monotonic progression check
    ts_ok, ts_msg = check_timestamps(lines)
    if not ts_ok:
        print(format_row(name, args_display, dur_str, FAIL_BADGE, ts_msg))
        failed_count += 1
        return False

    # 3. Death detection and timing validation
    death_lines = [l for l in lines if "died" in l]
    if expected_death is True:
        if not death_lines:
            print(format_row(name, args_display, dur_str, FAIL_BADGE, "no philosopher died"))
            failed_count += 1
            return False
        death_ts = int(death_lines[0].split()[0])
        if min_death_ts is not None and death_ts < min_death_ts:
            print(format_row(name, args_display, dur_str, FAIL_BADGE, f"died too early: {death_ts}ms < {min_death_ts}ms"))
            failed_count += 1
            return False
        if max_death_ts is not None and death_ts > max_death_ts:
            print(format_row(name, args_display, dur_str, FAIL_BADGE, f"died too late: {death_ts}ms > {max_death_ts}ms"))
            failed_count += 1
            return False
    elif expected_death is False:
        if death_lines:
            death_ts = death_lines[0].split()[0]
            print(format_row(name, args_display, dur_str, FAIL_BADGE, f"unexpected death at {death_ts}ms"))
            failed_count += 1
            return False

    print(format_row(name, args_display, dur_str, PASS_BADGE))
    passed_count += 1
    return True

def run_tsan_check():
    global passed_count, failed_count
    print_section("6. ThreadSanitizer Concurrency & Data-Race Audit")

    tsan_bin = "./philo_tsan"
    cflags = ["cc", "-Wall", "-Wextra", "-Werror", "-pthread", "-O3", "-Iinclude", "-fsanitize=thread", "-g"]
    srcs = ["src/main.c", "src/parsing.c", "src/monitor.c", "src/routine.c", "src/utils.c"]
    
    compile_proc = subprocess.run(cflags + srcs + ["-o", tsan_bin], 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if compile_proc.returncode != 0:
        print(format_row("TSan Compilation", "gcc -fsanitize", "0.00s", FAIL_BADGE, "compilation failed"))
        failed_count += 1
        return

    # Check 1: 4 Philosopher multi-cycle concurrency under TSan
    t0 = time.time()
    proc = subprocess.run([tsan_bin, "4", "410", "200", "200", "2"], 
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=8)
    dur = time.time() - t0
    if "ThreadSanitizer: data race" in proc.stderr or "WARNING: ThreadSanitizer" in proc.stderr:
        print(format_row("TSan Multi-Thread Concurrency", "4 410 200 200 2", f"{dur:.2f}s", FAIL_BADGE, "data race detected"))
        failed_count += 1
    else:
        print(format_row("TSan Multi-Thread Concurrency", "4 410 200 200 2", f"{dur:.2f}s", PASS_BADGE, "zero races"))
        passed_count += 1

    # Check 2: Single philosopher death under TSan
    t0 = time.time()
    proc = subprocess.run([tsan_bin, "1", "200", "100", "100"], 
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
    dur = time.time() - t0
    if "ThreadSanitizer: data race" in proc.stderr or "WARNING: ThreadSanitizer" in proc.stderr:
        print(format_row("TSan Death Termination", "1 200 100 100", f"{dur:.2f}s", FAIL_BADGE, "data race on death"))
        failed_count += 1
    else:
        print(format_row("TSan Death Termination", "1 200 100 100", f"{dur:.2f}s", PASS_BADGE, "zero races"))
        passed_count += 1

    if os.path.exists(tsan_bin):
        os.remove(tsan_bin)

def main():
    global suite_start_time
    if not os.path.isfile(PHILO_BIN):
        print(f"{RED}Error: Executable '{PHILO_BIN}' not found. Run 'make' first.{RESET}")
        sys.exit(1)

    suite_start_time = time.time()

    print(f"\n{BOLD}{WHITE}╔═════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{WHITE}║                   42 PHILOSOPHERS - HARD TEST SUITE                         ║{RESET}")
    print(f"{BOLD}{WHITE}║         Thread Synchronization, Timing Precision & Concurrency Audit        ║{RESET}")
    print(f"{BOLD}{WHITE}╚═════════════════════════════════════════════════════════════════════════════╝{RESET}")

    # 1. Input parsing
    print_section("1. Argument Parsing & Edge-Case Validation")
    run_test("No arguments provided", [], should_error=True)
    run_test("Negative philosopher count", ["-5", "800", "200", "200"], should_error=True)
    run_test("Zero philosopher count", ["0", "800", "200", "200"], should_error=True)
    run_test("Negative time-to-die", ["4", "-800", "200", "200"], should_error=True)
    run_test("Zero time-to-eat", ["4", "800", "0", "200"], should_error=True)
    run_test("Negative meal threshold", ["4", "800", "200", "200", "-1"], should_error=True)
    run_test("Zero meal threshold", ["4", "800", "200", "200", "0"], should_error=True)
    run_test("Non-numeric alphanumeric argument", ["4", "800", "200", "abc"], should_error=True)
    run_test("Too many arguments (> 5 parameters)", ["4", "800", "200", "200", "5", "6"], should_error=True)
    run_test("Integer overflow value (> INT_MAX)", ["99999999999999", "800", "200", "200"], should_error=True)
    run_test("Empty string parameter", ["", "800", "200", "200"], should_error=True)
    run_test("Standalone sign parameter", ["+", "800", "200", "200"], should_error=True)
    run_test("Supported positive '+' prefix", ["+4", "410", "200", "200", "1"], expected_death=False, timeout=3)

    # 2. Single Philosopher
    print_section("2. Single Philosopher (Deadlock & Double-Lock Prevention)")
    run_test("Single philo standard death", ["1", "800", "200", "200"], 
             expected_death=True, min_death_ts=800, max_death_ts=815, timeout=3)
    run_test("Single philo fast starvation", ["1", "300", "100", "100"], 
             expected_death=True, min_death_ts=300, max_death_ts=315, timeout=2)

    # 3. Death Timing Precision (< 15ms margin)
    print_section("3. Death Timing Precision (< 15ms tolerance)")
    run_test("Tight margin death timing", ["4", "310", "200", "100"], 
             expected_death=True, min_death_ts=310, max_death_ts=325, timeout=3)
    run_test("Immediate starvation", ["2", "100", "150", "150"], 
             expected_death=True, min_death_ts=100, max_death_ts=115, timeout=2)

    # 4. Meal Completion (No Death)
    print_section("4. Meal Threshold & Clean Process Termination")
    run_test("Even 4 philosophers, 3 meals", ["4", "410", "200", "200", "3"], 
             expected_death=False, timeout=5)
    run_test("Odd 5 philosophers, 5 meals", ["5", "800", "200", "200", "5"], 
             expected_death=False, timeout=8)
    run_test("Pair 2 philosophers, 4 meals", ["2", "800", "200", "200", "4"], 
             expected_death=False, timeout=6)

    # 5. High Load Concurrency Stress Tests
    print_section("5. Concurrency Stress (High Thread Counts)")
    run_test("50 philosopher threads, 3 meals", ["50", "800", "100", "100", "3"], 
             expected_death=False, timeout=10)
    run_test("100 philosopher threads, 2 meals", ["100", "800", "100", "100", "2"], 
             expected_death=False, timeout=12)
    run_test("198 philosopher threads, 2 meals", ["198", "800", "100", "100", "2"], 
             expected_death=False, timeout=15)

    # 6. ThreadSanitizer
    run_tsan_check()

    kill_philo()

    # Final summary card
    total_time = time.time() - suite_start_time
    total = passed_count + failed_count
    pct = (passed_count / total * 100) if total else 0

    print(f"\n{BOLD}{WHITE}╔═════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{WHITE}║                              TEST RUN SUMMARY                               ║{RESET}")
    print(f"{BOLD}{WHITE}╠═════════════════════════════════════════════════════════════════════════════╣{RESET}")
    print(f"{BOLD}{WHITE}║  {CYAN}Total Tests Executed{RESET}{BOLD}{WHITE} : {WHITE}{total:<10}{BOLD}{WHITE}  │  {CYAN}Elapsed Time{RESET}{BOLD}{WHITE} : {WHITE}{total_time:.2f}s{RESET}")
    print(f"{BOLD}{WHITE}║  {GREEN}Passed Cases        {RESET}{BOLD}{WHITE} : {GREEN}{passed_count:<10}{BOLD}{WHITE}  │  {YELLOW}Success Rate{RESET}{BOLD}{WHITE} : {GREEN if pct == 100 else RED}{pct:.1f}%{RESET}")
    print(f"{BOLD}{WHITE}║  {RED}Failed Cases        {RESET}{BOLD}{WHITE} : {RED}{failed_count:<10}{BOLD}{WHITE}  │  {CYAN}Architecture{RESET}{BOLD}{WHITE} : {WHITE}POSIX pthreads{RESET}")
    print(f"{BOLD}{WHITE}╚═════════════════════════════════════════════════════════════════════════════╝{RESET}\n")

    sys.exit(0 if failed_count == 0 else 1)

if __name__ == "__main__":
    main()
