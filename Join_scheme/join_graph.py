import ast
import numpy as np

OPS = {
    '>': np.greater,
    '<': np.less,
    '>=': np.greater_equal,
    '<=': np.less_equal,
    '=': np.equal,
    '==': np.equal
}

def process_condition(cond, tables_all=None):
    # parse a condition, either filter predicate or join operation
    start = None
    join = False
    join_keys = {}
    cond = cond.replace(" in ", " IN ")
    cond = cond.replace(" not in ", " NOT IN ")
    cond = cond.replace(" like ", " LIKE ")
    cond = cond.replace(" not like ", " NOT LIKE ")
    cond = cond.replace(" between ", " BETWEEN ")
    s = None
    ops = None

    if ' IN ' in cond:
        s = cond.split(' IN ')
        ops = "in"
    elif " NOT IN " in cond:
        s = cond.split(' NOT IN ')
        ops = "not in"
    elif " LIKE " in cond:
        s = cond.split(' LIKE ')
        ops = "like"
    elif " NOT LIKE " in cond:
        s = cond.split(' NOT LIKE ')
        ops = "not like"
    elif " BETWEEN " in cond:
        s = cond.split(' BETWEEN ')
        ops = "between"
    elif " IS " in cond:
        s = cond.split(' IS ')
        ops = OPS["="]

    if ' IN ' in cond or " NOT IN " in cond:
        attr = s[0].strip()
        try:
            value = list(ast.literal_eval(s[1].strip()))
        except:
            temp_value = s[1].strip()[1:][:-1].split(',')
            value = []
            for v in temp_value:
                value.append(v.strip())
        if tables_all:
            table = tables_all[attr.split(".")[0].strip()]
            attr = table + "." + attr.split(".")[-1].strip()
        else:
            table = attr.split(".")[0].strip()
        return table, [attr, ops, value], join, join_keys

    elif s is not None:
        attr = s[0].strip()
        value = s[1].strip()
        if tables_all:
            table = tables_all[attr.split(".")[0].strip()]
            attr = table + "." + attr.split(".")[-1].strip()
        else:
            table = attr.split(".")[0].strip()
        return table, [attr, ops, value], join, join_keys

    for i in range(len(cond)):
        s = cond[i]
        if s in OPS:
            start = i
            if cond[i + 1] in OPS:
                end = i + 2
            else:
                end = i + 1
            break

    if start is None:
        return None, [None, None, None], join, join_keys
    assert start is not None
    left = cond[:start].strip()
    ops = cond[start:end].strip()
    right = cond[end:].strip()
    table1 = left.split(".")[0].strip().lower()
    if tables_all:
        cond = cond.replace(table1 + ".", tables_all[table1] + ".")
        table1 = tables_all[table1]
        left = table1 + "." + left.split(".")[-1].strip()
    if "." in right:
        table2 = right.split(".")[0].strip().lower()
        if table2 in tables_all:
            cond = cond.replace(table2 + ".", tables_all[table2] + ".")
            table2 = tables_all[table2]
            right = table2 + "." + right.split(".")[-1].strip()
            join = True
            join_keys[table1] = left
            join_keys[table2] = right
            return table1 + " " + table2, cond, join, join_keys

    value = right.strip()
    if value[0] == "'" and value[-1] == "'":
        value = value[1:-1]
    try:
        value = list(ast.literal_eval(value.strip()))
    except:
        try:
            value = int(value)
        except:
            try:
                value = float(value)
            except:
                value = value

    return table1, [left, ops, value], join, join_keys


def process_condition_join(cond, tables_all):
    start = None
    join = False
    join_keys = {}
    for i in range(len(cond)):
        s = cond[i]
        if s == "=":
            start = i
            if cond[i + 1] == "=":
                end = i + 2
            else:
                end = i + 1
            break

    if start is None:
        return None, None, False, None

    left = cond[:start].strip()
    ops = cond[start:end].strip()
    right = cond[end:].strip()
    table1 = left.split(".")[0].strip().lower()
    if table1 in tables_all:
        left = tables_all[table1] + "." + left.split(".")[-1].strip()
    else:
        return None, None, False, None
    if "." in right:
        table2 = right.split(".")[0].strip().lower()
        if table2 in tables_all:
            right = tables_all[table2] + "." + right.split(".")[-1].strip()
            join = True
            join_keys[table1] = left
            join_keys[table2] = right
            return table1 + " " + table2, cond, join, join_keys
    return None, None, False, None


def parse_query_all_join(query):
    """
    This function will parse out all join conditions from the query.
    """
    query = query.replace(" where ", " WHERE ")
    query = query.replace(" from ", " FROM ")
    # query = query.replace(" and ", " AND ")
    query = query.split(";")[0]
    query = query.strip()
    tables_all = {}
    join_cond = {}
    join_keys = {}
    tables_str = query.split(" WHERE ")[0].split(" FROM ")[-1]
    for table_str in tables_str.split(","):
        table_str = table_str.strip()
        if " as " in table_str:
            tables_all[table_str.split(" as ")[-1]] = table_str.split(" as ")[0]
        else:
            tables_all[table_str.split(" ")[-1]] = table_str.split(" ")[0]
    conditions = query.split(" WHERE ")[-1].split(" AND ")

    add_all_equi_join = True

    if add_all_equi_join:
        equi_group = dict()
        def add_edge(k1, k2):
            if k1 in equi_group:
                if k2 in equi_group:
                    temp = equi_group[k1].union(equi_group[k2])
                    equi_group[k1] = temp.copy()
                    equi_group[k2] = temp.copy()
                else:
                    equi_group[k2] = equi_group[k1].copy()
            else:
                if k2 in equi_group:
                    equi_group[k1] = equi_group[k2].copy()
                else:
                    equi_group[k1] = set()
                    equi_group[k2] = set()
            equi_group[k1].add(k2)
            equi_group[k2].add(k1)

    for cond in conditions:
        cond = cond.strip()
        if cond[0] == "(" and cond[-1] == ")":
            cond = cond[1:-1]
        table, cond, join, join_key = process_condition_join(cond, tables_all)

        if join:
            if add_all_equi_join:
                [key1, key2] = cond.split("=")
                key1 = key1.strip()
                key2 = key2.strip()
                add_edge(key1, key2)
            for tab in join_key:
                if tab in join_keys:
                    join_keys[tab].add(join_key[tab])
                    join_cond[tab].add(cond)
                else:
                    join_keys[tab] = set([join_key[tab]])
                    join_cond[tab] = set([cond])

    if add_all_equi_join:
        for t in join_keys:
            for k in join_keys[t]:
                [_, c] = k.split(".")
                k = t + "." + c
                for other_k in equi_group[k]:
                    if k == other_k:
                        continue
                    other_t = other_k.split(".")[0]
                    cond1 = k + " = " + other_k
                    cond2 = other_k + " = " + k
                    if cond1 not in join_cond[t] and cond2 not in join_cond[t]:
                        assert cond1 not in join_cond[other_t]
                        assert cond2 not in join_cond[other_t]
                        join_cond[t].add(cond1)
                        join_cond[other_t].add(cond1)

    return tables_all, join_cond, join_keys

def find_equivalent_groups(pairs):
    groups = []
    for pair in pairs:
        found_group = None
        for group in groups:
            if pair[0] in group or pair[1] in group:
                found_group = group
                break

        if found_group:
            found_group.add(pair[0])
            found_group.add(pair[1])
        else:
            groups.append(set(pair))

    return groups

def get_join_hyper_graph(join_keys, org_equivalent_keys, tables_all, join_cond):
    #print('join_keys', join_keys)
    #print('org_equi', org_equivalent_keys)
    #print('tables_all', tables_all)
    #print('join_cond', join_cond)

    equivalent_group = dict()
    table_equivalent_group = dict()
    table_key_equivalent_group = dict()
    table_key_group_map = dict()

    equivalent_keys = dict()

    pairs = []
    for alias in join_cond:
        for cond in join_cond[alias]:
            [key1, key2] = cond.split("=")
            key1 = key1.strip()
            key2 = key2.strip()
            pairs.append((key1, key2))
    groups = find_equivalent_groups(pairs)
    for group in groups:
        header = None
        found = False
        for key in group:
            [alias, column] = key.split(".")
            table = tables_all[alias]
            org_key = table + '.' + column
            if org_key in org_equivalent_keys:
                found = True
                equivalent_keys[key] = set(group)
                break
            else:
                if header is None:
                    for org_PK in org_equivalent_keys:
                        if org_key in org_equivalent_keys[org_PK]:
                            header = org_PK
                else:
                    assert org_key in org_equivalent_keys[header], f'org_key {org_key} not in {org_equivalent_keys[header]} of header {header}'
        if not found:
            equivalent_keys[header] = set(group)
    assert len(equivalent_keys) == len(groups)

    for alias in join_keys:
        for key in join_keys[alias]:
            key = alias + "." + key.split(".")[1]
            seen = False
            for indicator in equivalent_keys:
                if key in equivalent_keys[indicator]:
                    if seen:
                        assert False, f"{key} appears in multiple equivalent groups."
                    if indicator not in equivalent_group:
                        equivalent_group[indicator] = [key]
                    else:
                        equivalent_group[indicator].append(key)
                    if alias not in table_key_equivalent_group:
                        table_key_equivalent_group[alias] = dict()
                        table_equivalent_group[alias] = set([indicator])
                        table_key_group_map[alias] = dict()
                        table_key_group_map[alias][key] = indicator
                    else:
                        table_equivalent_group[alias].add(indicator)
                        table_key_group_map[alias][key] = indicator
                    if indicator not in table_key_equivalent_group[alias]:
                        table_key_equivalent_group[alias][indicator] = [key]
                    else:
                        table_key_equivalent_group[alias][indicator].append(key)

                    seen = True
            if not seen:
                assert False, f"no equivalent groups found for {key}."
    return equivalent_group, table_equivalent_group, table_key_equivalent_group, table_key_group_map


def get_sub_query_equivalent_group(sub_tables, equivalent_group):
    ret = dict()

    for PK in equivalent_group:
        for key in equivalent_group[PK]:
            [alias, column] = key.split('.')
            if alias in sub_tables:
                if PK not in ret:
                    ret[PK] = []
                ret[PK].append(key)

    for PK in list(ret):
        if len(ret[PK]) < 2:
            del ret[PK]

    return ret


def parse_query_all_single_table(query):
    return


def parse_sub_plan_queries(psql_raw_file):
    with open(psql_raw_file, "r") as f:
        psql_raw = f.read()
    sub_plan_queries_raw = psql_raw.split("query: 0")[1:]
    sub_plan_queries_str_all = []
    for per_query in sub_plan_queries_raw:
        sub_plan_queries_str = []
        num_sub_plan_queries = len(per_query.split("query: "))
        all_info = per_query.split("RELOPTINFO (")[1:]
        assert num_sub_plan_queries * 2 == len(all_info)
        for i in range(num_sub_plan_queries):
            idx = i * 2
            table1 = all_info[idx].split("): rows=")[0]
            table2 = all_info[idx + 1].split("): rows=")[0]
            table_str = table1 + " " + table2
            sub_plan_queries_str.append(table_str)
        sub_plan_queries_str_all.append(sub_plan_queries_str)
    return sub_plan_queries_str_all


def get_PK(target, equivalent_keys):
    for PK in equivalent_keys:
        keys = equivalent_keys[PK]
        for key in keys:
            if key == target:
                return PK
    return None

def get_connected_PKs(PK, schema, equivalent_keys, tables_all):
    keys = equivalent_keys[PK]
    ret = []
    for key in keys:
        [table, col] = key.split(".")
        if tables_all is not None:
            assert False
            table_obj = schema.table_dictionary[tables_all[table]]
        else:
            table_obj = schema.table_dictionary[table]
        for attr in table_obj.attributes:
            print('get_PK', table + '.' + attr)
            connected_PK = get_PK(table + "." + attr, equivalent_keys)
            if connected_PK is not None:
                print('appending', connected_PK)
                ret.append(connected_PK)
    return ret

def dfs(PK, schema, equivalent_keys, tables_all=None, visited_PKs = []):
    assert tables_all is None
    print('dfs', PK)
    visited_PKs.append(PK)
    connected_PKs = get_connected_PKs(PK, schema, equivalent_keys, tables_all)
    for connected_PK in connected_PKs:
        if connected_PK not in visited_PKs:
            dfs(connected_PK, schema, equivalent_keys, tables_all, visited_PKs)

    return visited_PKs
