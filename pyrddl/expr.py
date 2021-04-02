# This file is part of pyrddl.

# pyrddl is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# pyrddl is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with pyrddl. If not, see <http://www.gnu.org/licenses/>.


from typing import Tuple, Sequence, Set, Union

Value = Union[bool, int, float]
ExprArg = Union['Expression', Tuple, str]


class Expression(object):
    '''Expression class represents a RDDL expression.

    Note:
        This class is intended to be solely used by the parser and compiler.
        Do not attempt to directly use this class to build an Expression object.

    Args:
        expr: Expression object or nested tuple of Expressions.
    '''

    def __init__(self, expr: Union['Expression', Tuple]) -> None:
        self._expr = expr

    def __getitem__(self, i):
        return self._expr[i]

    @property
    def etype(self) -> Tuple[str, str]:
        '''Returns the expression's type.'''
        if self._expr[0] in ['number', 'boolean']:
            return ('constant', str(type(self._expr[1])))
        elif self._expr[0] == 'pvar_expr':
            return ('pvar', self._expr[1][0])
        elif self._expr[0] == 'penum_expr':
            return ('penum', self._expr[1][0])
        elif self._expr[0] == 'randomvar':
            return ('randomvar', self._expr[1][0])
        elif self._expr[0] in ['+', '-', '*', '/']:
            return ('arithmetic', self._expr[0])
        elif self._expr[0] in ['^', '&', '|', '~', '=>', '<=>']:
            return ('boolean', self._expr[0])
        elif self._expr[0] in ['>=', '<=', '<', '>', '==', '~=']:
            return ('relational', self._expr[0])
        elif self._expr[0] == 'func':
            return ('func', self._expr[1][0])
        elif self._expr[0] == 'sum':
            return ('aggregation', 'sum')
        elif self._expr[0] == 'prod':
            return ('aggregation', 'prod')
        elif self._expr[0] == 'avg':
            return ('aggregation', 'avg')
        elif self._expr[0] == 'max':
            return ('aggregation', 'maximum')
        elif self._expr[0] == 'min':
            return ('aggregation', 'minimum')
        elif self._expr[0] == 'forall':
            return ('aggregation', 'forall')
        elif self._expr[0] == 'exists':
            return ('aggregation', 'exists')
        elif self._expr[0] == 'if':
            return ('control', 'if')
        else:
            return ('UNKOWN', 'UNKOWN')

    @property
    def args(self) -> Union[Value, Sequence[ExprArg]]:
        '''Returns the expression's arguments.'''
        if self._expr[0] in ['number', 'boolean']:
            return self._expr[1]
        elif self._expr[0] == 'pvar_expr':
            return self._expr[1]
        elif self._expr[0] == 'penum_expr':
            return self._expr[1]
        elif self._expr[0] == 'randomvar':
            return self._expr[1][1]
        elif self._expr[0] in ['+', '-', '*', '/']:
            return self._expr[1]
        elif self._expr[0] in ['^', '&', '|', '~', '=>', '<=>']:
            return self._expr[1]
        elif self._expr[0] in ['>=', '<=', '<', '>', '==', '~=']:
            return self._expr[1]
        elif self._expr[0] == 'func':
            return self._expr[1][1]
        elif self._expr[0] in ['sum', 'prod', 'avg', 'max', 'min', 'forall', 'exists']:
            return self._expr[1]
        elif self._expr[0] == 'if':
            return self._expr[1]
        else:
            return []

    def is_constant_expression(self) -> bool:
        '''Returns True if constant expression. False, othersize.'''
        return self.etype[0] == 'constant'

    def is_pvariable_expression(self) -> bool:
        '''Returns True if pvariable expression. False, otherwise.'''
        return self.etype[0] == 'pvar'

    @property
    def name(self) -> str:
        '''Returns the name of pvariable.

        Returns:
            Name of pvariable.

        Raises:
            ValueError: If not a pvariable expression.
        '''
        if not self.is_pvariable_expression():
            raise ValueError('Expression is not a pvariable.')
        return self._pvar_to_name(self.args)

    @property
    def value(self):
        '''Returns the value of a constant expression.

        Returns:
            Value of constant.

        Raises:
            ValueError: If not a constant expression.
        '''
        if not self.is_constant_expression():
            raise ValueError('Expression is not a number.')
        return self.args

    def __str__(self) -> str:
        '''Returns string representing the expression.'''
        return self.__expr_str(self, 0)

    @classmethod
    def __expr_str(cls, expr, level):
        '''Returns string representing the expression.'''
        ident = ' ' * level * 4

        if isinstance(expr, tuple):
            return '{}{}'.format(ident, str(expr))

        if expr.etype[0] in ['pvar', 'constant', 'penum']:
            return '{}Expression(etype={}, args={})'.format(ident, expr.etype, expr.args)

        if not isinstance(expr, Expression):
            return '{}{}'.format(ident, str(expr))

        args = list(cls.__expr_str(arg, level + 1) for arg in expr.args)
        args = '\n'.join(args)
        return '{}Expression(etype={}, args=\n{})'.format(ident, expr.etype, args)

    @property
    def scope(self) -> Set[str]:
        '''Returns the set of fluents in the expression's scope.

        Returns:
            The set of fluents in the expression's scope.
        '''
        return self.__get_scope(self._expr)

    @classmethod
    def __get_scope(cls,
            expr: Union['Expression', Tuple]) -> Set[str]:
        '''Returns the set of fluents in the expression's scope.

        Args:
            expr: Expression object or nested tuple of Expressions.

        Returns:
            The set of fluents in the expression's scope.
        '''
        scope = set()
        for i, atom in enumerate(expr):
            if isinstance(atom, Expression):
                scope.update(cls.__get_scope(atom._expr))
            elif type(atom) in [tuple, list]:
                scope.update(cls.__get_scope(atom))
            elif atom == 'pvar_expr':
                functor, params = expr[i+1]
                arity = len(params) if params is not None else 0
                name = '{}/{}'.format(functor, arity)
                scope.add(name)
                break
        return scope

    @classmethod
    def _pvar_to_name(cls, pvar_expr):
        '''Returns the name of pvariable.

        Returns:
            Name of pvariable.
        '''
        functor = pvar_expr[0]
        arity = len(pvar_expr[1]) if pvar_expr[1] is not None else 0
        return '{}/{}'.format(functor, arity)
