import pstats,glob

for file in glob.glob('*.prof'):
    pstats.Stats(file).strip_dirs().sort_stats("time").print_stats(20)
