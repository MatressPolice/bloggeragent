import timeit

baseline_setup = "import datetime"
baseline_code = """
instruction = f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}"
"""

opt_setup = "import datetime"
opt_code = """
def get_instruction(context=None):
    return f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}"
instruction = get_instruction
"""

print("Baseline (evaluate string):", timeit.timeit(baseline_code, setup=baseline_setup, number=1000000))
print("Optimized (define function):", timeit.timeit(opt_code, setup=opt_setup, number=1000000))
