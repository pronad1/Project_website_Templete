import re, sys, glob
RUN = re.compile(r"(?:[\u0980-\u09FF\u200c\u200d]+(?:[ \u0964\u0965]+[\u0980-\u09FF\u200c\u200d]+)*[\u0964\u0965]?)|[\u0964\u0965]+")
def wrap(text):
    return RUN.sub(lambda m: r"\bn{" + m.group(0) + "}", text)
if __name__ == "__main__":
    for path in sys.argv[1:]:
        s = open(path, encoding="utf-8").read()
        s = re.sub(r"\\bn\{([^{}]*)\}", r"\1", s)        # idempotent: unwrap first
        open(path, "w", encoding="utf-8").write(wrap(s))
