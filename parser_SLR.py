# coding:utf-8
import re
from collections import namedtuple

operators = ['shift', 'reduce', 'accept', 'error']


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


Item = namedtuple('Item', ['prod', 'pos'])
# use tuple of production and positon of dot to represent item


class SLR:
    def __init__(self):
        self.start_symbol = None
        self.start_symbol_copy = None  # 为了再扩展文法之后依旧能够记住开始符
        self.prods = []
        self.firsts = []
        self.vn = set()  # 非终结符
        self.symbols = set()
        self.added = {}
        self.ana_stack = []
        self.ana_buffer = []
        self.ana_table = {}
        self.itemsets = []

    def add_production(self, prod):
        group = re.split("\s|->|\n|\|*", prod)
        left = group[0]  # left part 左部
        self.vn.add(left)
        self.symbols.add(left)
        # right = set(group[1:-1] - '')
        if self.start_symbol is None:
            self.start_symbol = left
            self.start_symbol_copy = left
        right = set(group[1:-1])
        right.remove('')  # right part 右部
        for item in right:
            self.prods.append(Production(left, item))
            for symbol in item:
                self.symbols.add(symbol)
        for nt in self.vn:
            self.added[nt] = False

    def readin(self, file):
        with open(file) as f:
            for line in f:
                self.add_production(line)
        f.close()

    def _cal_closure(self, item):
        res = set()
        curr_ch = item.prod.right[item.pos] if item.pos < len(
            item.prod.right) else None
        if self.added.get(curr_ch, True) is False:
            for pd in self.prods:
                if pd.left == curr_ch:
                    res.add(Item(pd, 0))
        # print(res)
        return res

    def closure(self, itemset):
        res = itemset.copy()
        length = -1
        while(len(res) != length):  # add item until size not change
            length = len(res)
            for item in res:
                tmp_set = self._cal_closure(item)
                # print(tmp_set)
                res = res.union(tmp_set)
                # print(length, 'res', res)
        for key in self.added:
            self.added[key] = False
        return res

    def goto(self, itemset, ch):
        res = set()
        for item in itemset:
            if item.pos < len(item.prod.right):
                if item.prod.right[item.pos] == ch:
                    tmp_item = Item(item.prod, item.pos + 1)
                    # put dot to the next pos
                    tmp_set = set()
                    tmp_set.add(tmp_item)
                    res = res.union(self.closure(tmp_set))
        return res

    def extend_grammar(self):
        new_start_symbol = 'Z' if self.start_symbol != 'Z' else 'E'
        new_pd = Production(new_start_symbol, self.start_symbol)
        self.prods.append(new_pd)
        tmp_set = set()
        tmp_set.add(Item(new_pd, 0))
        c = self.closure(tmp_set)
        self.itemsets.append(c)
        self.start_symbol = new_start_symbol

        length = -1
        count = 0
        while len(self.itemsets) != length:
            length = len(self.itemsets)
            for itemset in self.itemsets[count:]:
                count += 1
                for symbol in self.symbols:
                    # print('goto(c, ', symbol, ')', self.goto(c, symbol), len(self.goto(c, symbol)))
                    gt = self.goto(itemset, symbol)
                    if gt and gt not in self.itemsets:
                        self.itemsets.append(gt)

    def _first(self, rhs):  # calculate first set
        res = set()
        if rhs[0].isupper():
            for pd in self.prods:
                if pd.left == rhs[0]:
                    if (pd.right == '~' and len(pd.right) == 1) or pd.right[0] == pd.left:
                        pass
                    elif self._first(pd.right) is not None:
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
                if Production(nt, '~') not in self.prods:
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

    def _gen_ana_table(self):
        for i in range(len(self.itemsets)):
            if Item(Production(self.start_symbol, self.start_symbol_copy), 1) in self.itemsets[i]:
                self.ana_table[(i, '#')] = ('accept', None)
            for item in self.itemsets[i]:
                if item.pos == len(item.prod.right):  # A -> α·
                    # 并且 A不是Z(扩展文法的新开始符号)
                    if item.prod.left != self.start_symbol:
                        for tn in self._follow(item.prod.left):
                            self.ana_table[(i, tn)] = ('reduce', item.prod)
                elif item.prod.right[item.pos] not in self.vn:  # A->α·aβ
                    tn = item.prod.right[item.pos]
                    s = self.goto(self.itemsets[i], tn)
                    if s in self.itemsets:
                        pos = self.itemsets.index(s)
                        self.ana_table[(i, tn)] = ('shift', pos)
            for nt in self.vn:
                s = self.goto(self.itemsets[i], nt)
                if s in self.itemsets:
                    pos = self.itemsets.index(s)
                    self.ana_table[(i, nt)] = pos

    def run(self):
        self.extend_grammar()
        self._gen_ana_table()

    def parse(self, sentence):
        sentence = sentence + '#'
        ip = 0
        
        self.ana_stack.append(0)
        while(len(self.ana_stack) > 0):
            top = self.ana_stack[-1]
            symbol = sentence[ip]
            print('top: ', top, 'symbol: ', symbol)
            op, prod = self.ana_table.get((top, symbol), ('error', None))
            print(op, prod)
            if op == 'shift':
                self.ana_stack.append(symbol)
                self.ana_stack.append(prod)
                ip += 1
                print('stack: ', self.ana_stack)
            elif op == 'reduce':
                length = len(prod.right)
                while length > 0:
                    self.ana_stack.pop()
                    self.ana_stack.pop()
                    length -= 1
                s = self.ana_stack[-1]
                self.ana_stack.append(prod.left)
                self.ana_stack.append(self.ana_table[(s, prod.left)])
                # print(prod)
                print('stack: ', self.ana_stack)
            elif op == 'accept':
                print('Accepted!')
                return
            else:
                print('Not Accepted!')
                return


def main():
    parser = SLR()
    parser.readin('parser.in')
    parser.run()
    parser.parse('i*i-i')
    # print(parser.ana_table[(0, 'i')])


if __name__ == '__main__':
    main()
