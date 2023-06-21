# make all pairwise combinations of model and task
with open('tasks.txt') as f:
    tasks = f.read().split('\n')
    tasks = [t for t in tasks if '#' not in t]
with open('models.txt') as f:
    models = f.read().split('\n')
    models = [m for m in models if '#' not in m]
s = 'model,task\n' + "\n".join([model+","+task for model in models for task in tasks])
with open('model-task.csv', 'w') as f:
    f.write(s)