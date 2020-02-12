find . -type f -name '*.jpeg' -print0 | xargs -0 rename 's/\.jpeg/\.JPG/'
