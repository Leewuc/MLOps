def run_postprocess_task(args, tasks):  # 함수 추가
    processor = tasks.get_process(args.task)

    postprocess = processor(args)
    postprocess.run()


def main(args):
    # ...
    func_map = {
        …
        tasks.POST_PROCESS: run_postprocess_task,  # 추가
    }
