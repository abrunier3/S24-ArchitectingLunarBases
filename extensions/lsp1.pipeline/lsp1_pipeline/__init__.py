try:
    from .extension import LSP1PipelineExtension
except ModuleNotFoundError as exc:
    if exc.name != "omni":
        raise
    LSP1PipelineExtension = None
