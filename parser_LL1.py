import re


class production:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return 'left:{0.left}, right:{0.right}'.format(self)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash((self.left, self.right))


class LL1:
    def __init__(self):
        self.prods = []
        self.start_symbol = None
        self.selects = {}
        self.ana_table = {}
        self.ana_stack = []

    def __repr__(self):
        return 'VT:{0.VT}, VN.{0.VN}'.format(self)

    def add_production(self, prod):
        group = re.split("\s|->|\n|\|*", prod)
        left = group[0]  # left part 左部
        # right = set(group[1:-1] - '')
        if self.start_symbol is None:
            self.start_symbol = left
        right = set(group[1:-1])
        right.remove('')  # right part 右部
        for item in right:
            self.prods.append(production(left, item))

    def readin(self, file):
        with open(file) as f:
            for line in f:
                self.add_production(line)
        f.close()

    def _first(self, rhs):  # calculate first set
        res = set()
        if rhs[0].isupper():
            for pd in self.prods:
                if pd.left == rhs[0]:
                    if pd.right == '~' and len(pd.right) == 1:
                        pass
                    else:
                        res = res.union(self._first(pd.right))

        elif rhs == '~' and len(rhs) == 1:
            pass
        else:  # is terminal
            res.add(rhs[0])
        return res

    def _is_none(self, rhs):  # judge if can be None
        if rhs == '~':
            return True
        if rhs.isupper():
            for nt in rhs:
                if production(nt, '~') not in self.prods:
                    return False
            return True
        return False

    def _follow(self, lhs):  # calculate follow set
        '''B -> ...Aβ'''
        if lhs == self.start_symbol:
            res = set('#')
        else:
            res = set('')
        for pd in self.prods:
            pos = pd.right.find(lhs)
            if pos != -1:
                if pos == len(pd.right) - 1:  # β is None
                    if lhs != pd.left:
                        res = res.union(self._follow(pd.left))
                else:
                    # β can't be None
                    res = res.union(self._first(pd.right[pos + 1:]))
                    if self._is_none(pd.right[pos + 1:]):  # β can be None
                        res = res.union(self._follow(pd.left))
        return res

    def _select(self, prod):
        if self._is_none(prod.right):
            return self._first(prod.right).union(self._follow(prod.left))
        else:
            return self._first(prod.right)

    def gen_ana_table(self):
        for pd, select in self.selects.items():
            for element in select:
                self.ana_table[(pd.left, element)] = pd.right

    def is_valid(self):
        dic = {}
        for prod, slct in self.selects.items():
            if prod.left not in dic:
                dic[prod.left] = slct
            elif not (slct & dic[prod.left]):
                dic[prod.left] = slct
            else:
                return False
        return True

    def parse(self, sentence):
        sentence = sentence + '#'
        self.ana_stack.append('#')
        self.ana_stack.append(self.start_symbol)

        pos = 0
        while len(self.ana_stack) > 0:
            top = self.ana_stack[-1]  # the top element
            print('STACK:', self.ana_stack, 'TOP:', top)
            if top == sentence[pos]:
                self.ana_stack.pop()
                pos += 1
            elif (top, sentence[pos]) not in self.ana_table:
                print('Not Accepted!')
                return
            else:  # find in ana_table
                if self.ana_table[(top, sentence[pos])] == '~':
                    self.ana_stack.pop()
                else:
                    self.ana_stack.pop()  # pop the top
                    # reverse push in ana_stack
                    for item in self.ana_table[(
                            top, sentence[pos])][::-1]:
                        self.ana_stack.append(item)
        print('Accepted!')

    def run(self):
        for pd in self.prods:
            self.selects[pd] = self._select(pd)
        self.gen_ana_table()
        if self.is_valid():
            print('This grammar is valid for LL(1)')
        else:
            print('This grammar is not valid for LL(1)')


def main():
    parser = LL1()
    parser.readin('parser2.in')
    parser.run()
    parser.parse('a*(a+a)')


if __name__ == '__main__':
    main()
