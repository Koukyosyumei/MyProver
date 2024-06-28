import ast
import inspect

from .hoare import weakest_precondition
from .type import TypeBOOL
from .parser import Parser
from .visitor import Py2AssernTranslator


def verify_func(func, scope, inputs, requires, ensures):
    code = inspect.getsource(func)
    func_ast = ast.parse(code)
    mp_ast = Py2AssernTranslator().visit(func_ast)
    
