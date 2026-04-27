def func(**kwargs):
    print(kwargs)
    if 'name' in kwargs:
        print(f"Hello, {kwargs['name']}!")

func(name="Ivan", age=22, word="y.o")
