# coding:utf-8

import re


class Production:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return 'left:{0.left}, right:{0.right}'.format(self)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash((self.left, self.right))


class OperPre:
    def __init__(self):
        self.prods = []
        self.start_symbol = None
        self.vn = set()  # nonterminal 非终结符
        self.vt = set()  # terminal 终结符
        self.pre_matrix = {}
        self.ana_stack = []  # analyze stack 分析栈
        self.buffer = []  # 缓冲区
        self.firstvt = {}
        self.lastvt = {}

    def __repr__(self):
        return 'VT:{0.VT}, VN.{0.VN}'.format(self)

    def add_production(self, prod):
        group = re.split("\s|->|\n|\|*", prod)
        left = group[0]  # left part 左部
        self.vn.add(left)
        # right = set(group[1:-1] - '')
        if self.start_symbol is None:
            self.start_symbol = left
        right = set(group[1:-1])
        right.remove('')  # right part 右部
        for item in right:
            self.prods.append(Production(left, item))
            for symbol in item:
                if symbol.isupper() is False and symbol != '~':  # not nonterminal and not none
                    self.vt.add(symbol)

    def readin(self, file):
        with open(file) as f:
            for line in f:
                self.add_production(line)
        f.close()

    def _is_none(self, rhs):  # judge if can be None
        if rhs == '~':
            return True
        if rhs.isupper():
            for nt in rhs:
                if Production(nt, '~') not in self.prods:
                    return False
            return True
        return False

    def _invalid(self, rhs):
        for index in range(len(rhs) - 1):
            if rhs[index] in self.vn and rhs[index + 1] in self.vn:
                return True
        return False

    def _is_valid(self):
        for prod in self.prods:
            if self._invalid(prod.right):
                return False
        return True

    def _first(self, nt):  # helper function for firstvt
        res = set()
        for pd in self.prods:
            if pd.left == nt:
                if (pd.right == '~' and len(pd.right) == 1) or pd.right[0] == nt:
                    pass
                elif pd.right[0] in self.vn:
                    res = res.union(self._first(pd.right[0]))
                else:
                    res.add(pd.right[0])
        return res

    def _second(self, nt):  # helper function for firstvt
        res = set()
        for pd in self.prods:
            if nt == pd.left:
                if pd.right[0] in self.vn:  # the last is nonterminal
                    if len(pd.right) > 1:
                        res.add(pd.right[1])
                        if pd.right[0] != nt:
                            res = res.union(self._second(pd.right[0]))
                    else:
                        res = res.union(self._second(pd.right[0]))
        return res

    def _firstvt(self, nt):
        return self._first(nt).union(self._second(nt))

    def _last(self, nt):
        res = set()
        for pd in self.prods:
            if pd.left == nt:
                # -> none or recursive
                if (pd.right == '~' and len(pd.right) == 1) or pd.right[-1] == nt:
                    pass
                elif pd.right[-1] in self.vn:  # the last is nonterminal
                    res = res.union(self._last(pd.right[-1]))
                else:
                    res.add(pd.right[-1])
        return res

    def _second_to_last(self, nt):
        res = set()
        for pd in self.prods:
            if pd.left == nt:
                if pd.right[-1] in self.vn:  # the last is nonterminal
                    if len(pd.right) > 1:
                        res.add(pd.right[-2])
                        if pd.right[-1] != nt:
                            res = res.union(self._second(pd.right[-1]))
                    else:
                        res = res.union(self._second(pd.right[-1]))
        return res

    def _lastvt(self, nt):
        return self._last(nt).union(self._second_to_last(nt))

    def _gen_pre_matrix(self):
        for pd in self.prods:
            for index in range(len(pd.right) - 1):
                # P -> ...ab...
                if pd.right[index] in self.vt and pd.right[index + 1] in self.vt:
                    self.pre_matrix[(
                        pd.right[index], pd.right[index + 1])] = '='
                # P -> ...Rb..
                if pd.right[index] in self.vn and pd.right[index + 1] in self.vt:
                    for tn in self.lastvt[pd.right[index]]:
                        self.pre_matrix[(tn, pd.right[index + 1])] = '>'
                # P -> ...Qb...
                if pd.right[index] in self.vt and pd.right[index + 1] in self.vn:
                    if index < len(pd.right) - 2:
                        # P -> ...aQb...
                        self.pre_matrix[(
                            pd.right[index], pd.right[index + 2])] = '='
                    for tn in self.firstvt[pd.right[index + 1]]:
                        self.pre_matrix[(pd.right[index], tn)] = '<'
            for tn in self.firstvt[self.start_symbol]:
                self.pre_matrix[('#', tn)] = '<'
            for tn in self.lastvt[self.start_symbol]:
                self.pre_matrix[(tn, '#')] = '>'
            self.pre_matrix[('#', '#')] = '='

    def parse(self, sentence):
        sentence = sentence + '#'
        self.ana_stack.append('#')
        pos = 0
        while True:
            print(self.ana_stack, sentence[pos:])
            if sentence[pos] == '#' and self.ana_stack[-1] == '#':
                print('Accepted')
                return
            else:
                top = self.ana_stack[-1]
                print('top', top)
                if self.pre_matrix.get((top, sentence[pos]), None) in ['=', '<']:
                    self.ana_stack.append(sentence[pos])
                    pos += 1
                elif self.pre_matrix.get((top, sentence[pos]), None) == '>':
                    while True:
                        p = self.ana_stack.pop()
                        top = self.ana_stack[-1]
                        print(self.ana_stack, sentence[pos:])
                        if self.pre_matrix.get((top, p), None) == '<':
                            break
                        elif top == sentence[pos] == '#':
                            break
                        elif (top, p) not in self.pre_matrix:
                            print(top, sentence[pos], 'Not Accepted!')
                            return
                else:
                    print('Not Accepted')
                    return

    def run(self):
        for nt in self.vn:
            self.firstvt[nt] = self._firstvt(nt)
            self.lastvt[nt] = self._lastvt(nt)
        self._gen_pre_matrix()
        if self._is_valid():
            print('This grammar is OG grammar')
        else:
            print('This grammar is not OG grammar')


def main():
    parser = OperPre()
    parser.readin('example.in')
    parser.run()
    print(parser.pre_matrix)
    parser.parse('(i+i)*i/i')
    # print(re.sub(num, 'i', '134+124'))


if __name__ == '__main__':
    main()
