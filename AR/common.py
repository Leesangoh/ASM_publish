"""Data abstractions."""
from abc import abstractmethod

from collections import defaultdict, namedtuple
import copy
import os
import time

import numpy as np
import pandas as pd

import torch
from torch.utils.data import Dataset, IterableDataset, Subset

import psycopg2

debug = False

TYPE_NORMAL_ATTR = 0
TYPE_INDICATOR = 1
TYPE_FANOUT = 2
table_dtype ={'aka_name': {'name': object,   'imdb_index': object,   'name_pcode_cf': object,   'name_pcode_nf': object,   'surname_pcode': object,   'md5sum': object},  'aka_title': {'title': object,   'imdb_index': object,   'phonetic_code': object,   'note': object,   'md5sum': object},  'cast_info': {'note': object},  'char_name': {'name': object,   'imdb_index': object,   'name_pcode_nf': object,   'surname_pcode': object,   'md5sum': object},  'comp_cast_type': {'kind': object},  'company_name': {'name': object,   'country_code': object,   'name_pcode_nf': object,   'name_pcode_sf': object,   'md5sum': object},  'company_type': {'kind': object},  'info_type': {'info': object},  'keyword': {'keyword': object, 'phonetic_code': object},  'kind_type': {'kind': object},  'link_type': {'link': object},  'movie_companies': {'note': object},  'movie_info_idx': {'info': object, 'note': object},  'name': {'name': object,   'imdb_index': object,   'gender': object,   'name_pcode_cf': object,   'name_pcode_nf': object,   'surname_pcode': object,   'md5sum': object},  'role_type': {'role': object},  'title': {'title': object,   'imdb_index': object,   'phonetic_code': object,   'series_years': object,   'md5sum': object},  'movie_info': {'info': object, 'note': object},  'person_info': {'info': object, 'note': object},   'customer_address': {'ca_address_id': object,   'ca_street_number': object,   'ca_street_name': object,   'ca_street_type': object,   'ca_suite_number': object,   'ca_city': object,   'ca_county': object,   'ca_state': object,   'ca_zip': object,   'ca_country': object,   'ca_location_type': object},  'customer_demographics': {'cd_gender': object,   'cd_marital_status': object,   'cd_education_status': object,   'cd_credit_rating': object},  'date_dim': {'d_date_id': object,   'd_day_name': object,   'd_quarter_name': object,   'd_holiday': object,   'd_weekend': object,   'd_following_holiday': object,   'd_current_day': object,   'd_current_week': object,   'd_current_month': object,   'd_current_quarter': object,   'd_current_year': object,   'd_date': object},  'warehouse': {'w_warehouse_id': object,   'w_warehouse_name': object,   'w_street_number': object,   'w_street_name': object,   'w_street_type': object,   'w_suite_number': object,   'w_city': object,   'w_county': object,   'w_state': object,   'w_zip': object,   'w_country': object},  'ship_mode': {'sm_ship_mode_id': object,   'sm_type': object,   'sm_code': object,   'sm_carrier': object,   'sm_contract': object},  'time_dim': {'t_time_id': object,   't_am_pm': object,   't_shift': object,   't_sub_shift': object,   't_meal_time': object},  'reason': {'r_reason_id': object, 'r_reason_desc': object},  'item': {'i_item_id': object,   'i_item_desc': object,   'i_brand': object,   'i_class': object,   'i_category': object,   'i_manufact': object,   'i_size': object,   'i_formulation': object,   'i_color': object,   'i_units': object,   'i_container': object,   'i_product_name': object,   'i_rec_start_date': object,   'i_rec_end_date': object},  'store': {'s_store_id': object,   's_store_name': object,   's_hours': object,   's_manager': object,   's_geography_class': object,   's_market_desc': object,   's_market_manager': object,   's_division_name': object,   's_company_name': object,   's_street_number': object,   's_street_name': object,   's_street_type': object,   's_suite_number': object,   's_city': object,   's_county': object,   's_state': object,   's_zip': object,   's_country': object,   's_rec_start_date': object,   's_rec_end_date': object},  'call_center': {'cc_call_center_id': object,   'cc_name': object,   'cc_class': object,   'cc_hours': object,   'cc_manager': object,   'cc_mkt_class': object,   'cc_mkt_desc': object,   'cc_market_manager': object,   'cc_division_name': object,   'cc_company_name': object,   'cc_street_number': object,   'cc_street_name': object,   'cc_street_type': object,   'cc_suite_number': object,   'cc_city': object,   'cc_county': object,   'cc_state': object,   'cc_zip': object,   'cc_country': object,   'cc_rec_start_date': object,   'cc_rec_end_date': object},  'customer': {'c_customer_id': object,   'c_salutation': object,   'c_first_name': object,   'c_last_name': object,   'c_preferred_cust_flag': object,   'c_birth_country': object,   'c_login': object,   'c_email_address': object},  'web_site': {'web_site_id': object,   'web_name': object,   'web_class': object,   'web_manager': object,   'web_mkt_class': object,   'web_mkt_desc': object,   'web_market_manager': object,   'web_company_name': object,   'web_street_number': object,   'web_street_name': object,   'web_street_type': object,   'web_suite_number': object,   'web_city': object,   'web_county': object,   'web_state': object,   'web_zip': object,   'web_country': object,   'web_rec_start_date': object,   'web_rec_end_date': object},  'household_demographics': {'hd_buy_potential': object},  'web_page': {'wp_web_page_id': object,   'wp_autogen_flag': object,   'wp_url': object,   'wp_type': object,   'wp_rec_start_date': object,   'wp_rec_end_date': object},  'promotion': {'p_promo_id': object,   'p_promo_name': object,   'p_channel_dmail': object,   'p_channel_email': object,   'p_channel_catalog': object,   'p_channel_tv': object,   'p_channel_radio': object,   'p_channel_press': object,   'p_channel_event': object,   'p_channel_demo': object,   'p_channel_details': object,   'p_purpose': object,   'p_discount_active': object},  'catalog_page': {'cp_catalog_page_id': object,   'cp_department': object,   'cp_description': object,   'cp_type': object}}

def logging(txt,header='',path="./results/log.txt"):
    torch.set_printoptions(profile="full")
    with open(path,'at') as writer:
        writer.write(f"{header}:{txt}\n")
    torch.set_printoptions(profile="default")  # reset

def loggingTensor(idx,logits, data,path="./results/") :
    logit_file_name = f"{idx:02d}_nin_logits.pt"
    data_file_name = f"{idx:02d}_nin_data.pt"

    torch.save(logits,path+logit_file_name)
    torch.save(data,path+data_file_name)

def time_this(f):

    def timed_wrapper(*args, **kw):
        start_time = time.time()
        result = f(*args, **kw)
        end_time = time.time()

        # Time taken = end_time - start_time
        print('| func:%r took: %2.4f seconds |' % \
              (f.__name__, end_time - start_time))
        return result

    return timed_wrapper


# Column factorization.
#
# See estimators::FactorizedProgressiveSampling::update_factor_mask for
# a description of dominant operators.
#
# What each operator projects to.
PROJECT_OPERATORS = {
    "<": "<=",
    ">": ">=",
    "!=": "ALL_TRUE",
    "<=": "<=",
    ">=": ">=",
}
# What each operator projects to for the last subvar, if not the same as other
# subvars.
PROJECT_OPERATORS_LAST = {
    "<": "<",
    ">": ">",
    "!=": "!=",
}
# What the dominant operator for each operator is.
PROJECT_OPERATORS_DOMINANT = {
    "<=": "<",
    ">=": ">",
    "<": "<",
    ">": ">",
    "!=": "!=",
}


class Column(object):
    """A column.  Data is write-once, immutable-after.

    Typical usage:
      col = Column('myCol').Fill(data).SetDistribution(domain_vals)

    "data" and "domain_vals" are NOT copied.
    """

    def __init__(self,
                 name,
                 distribution_size=None,
                 pg_name=None,
                 factor_id=None,
                 bit_width=None,
                 bit_offset=None,
                 domain_bits=None,
                 num_bits=None):
        self.name = name

        # Data related fields.
        self.data = None
        self.all_distinct_values = None
        self.distribution_size = distribution_size

        # Factorization related fields.
        self.factor_id = factor_id
        self.bit_width = bit_width
        self.bit_offset = bit_offset
        self.domain_bits = domain_bits
        self.num_bits = num_bits

        # pg_name is the name of the corresponding column in the Postgres db.
        if pg_name:
            self.pg_name = pg_name
        else:
            self.pg_name = name

    def Name(self):
        """Name of this column."""
        return self.name

    def DistributionSize(self):
        """This column will take on discrete values in [0, N).

        Used to dictionary-encode values to this discretized range.
        """
        return self.distribution_size

    def ProjectValue(self, value):
        """Bit slicing: returns the relevant bits in binary for a sub-var."""
        assert self.factor_id is not None, "Only for factorized cols"
        return (value >> self.bit_offset) & (2**self.bit_width - 1)

    def ProjectOperator(self, op):
        assert self.factor_id is not None, "Only for factorized cols"
        if self.bit_offset > 0:
            # If not found, no need to project.
            return PROJECT_OPERATORS.get(op, op)
        # Last subvar: identity (should not project).
        return op

    def ProjectOperatorDominant(self, op):
        assert self.factor_id is not None, "Only for factorized cols"
        return PROJECT_OPERATORS_DOMINANT.get(op, op)

    def BinToVal(self, bin_id):
        assert bin_id >= 0 and bin_id < self.distribution_size, bin_id
        return self.all_distinct_values[bin_id]

    def ValToBin(self, val):
        if isinstance(self.all_distinct_values, list):
            return self.all_distinct_values.index(val)
        inds = np.where(self.all_distinct_values == val)
        assert len(inds[0]) > 0, val

        return inds[0][0]

    def FindProjection(self, val):
        if val in self.all_distinct_values:
            return (self.ValToBin(val), True)
        elif val > self.all_distinct_values[-1]:
            return (len(self.all_distinct_values), False)
        elif val < self.all_distinct_values[0]:
            return (-1, False)
        else:
            return (next(
                i for i, v in enumerate(self.all_distinct_values) if v > val),
                    False)

    def SetDistribution(self, distinct_values):
        """This is all the values this column will ever see."""
        assert self.all_distinct_values is None
        # pd.isnull returns true for both np.nan and np.datetime64('NaT').
        is_nan = pd.isnull(distinct_values)
        contains_nan = np.any(is_nan)
        dv_no_nan = distinct_values[~is_nan]
        # IMPORTANT: np.sort puts NaT values at beginning, and NaN values
        # at end for our purposes we always add any null value to the
        # beginning.
        vs = np.sort(np.unique(dv_no_nan))
        if contains_nan and np.issubdtype(distinct_values.dtype, np.datetime64):
            vs = np.insert(vs, 0, np.datetime64('NaT'))
        elif contains_nan:
            vs = np.insert(vs, 0, np.nan)
        if self.distribution_size is not None:
            assert len(vs) == self.distribution_size, f'len(distinct_values) = {len(distinct_values)}, distribution_size = {self.distribution_size}, len(vs) = {len(vs)}'
        self.all_distinct_values = vs
        self.distribution_size = len(vs)
        return self

    def Fill(self, data_instance, infer_dist=False):
        assert self.data is None
        self.data = data_instance
        # If no distribution is currently specified, then infer distinct values
        # from data.
        if infer_dist:
            assert False
            self.SetDistribution(self.data)
        return self

    def InsertNullInDomain(self):
        # Convention: np.nan would only appear first.
        if not pd.isnull(self.all_distinct_values[0]):
            if self.all_distinct_values.dtype == np.dtype('object'):
                # String columns: inserting nan preserves the dtype.
                self.all_distinct_values = np.insert(self.all_distinct_values,
                                                     0, np.nan)
            else:
                # Assumed to be numeric columns.  np.nan is treated as a
                # float.
                self.all_distinct_values = np.insert(
                    self.all_distinct_values.astype(np.float64, copy=False), 0,
                    np.nan)
            self.distribution_size = len(self.all_distinct_values)

    def __repr__(self):
        return 'Column({}, distribution_size={})'.format(
            self.name, self.distribution_size)


class Table(object):
    """A collection of Columns."""

    def __init__(self, name, columns, pg_name=None, validate_cardinality=True):
        """Creates a Table.

        Args:
            name: Name of this table object.
            columns: List of Column instances to populate this table.
            pg_name: name of the corresponding table in Postgres.
        """
        self.name = name
        if validate_cardinality:
            self.cardinality = self._validate_cardinality(columns)
        else:
            # Used as a wrapper, not a real table.
            self.cardinality = None
        self.columns = columns

        # Bin to val funcs useful for sampling.  Takes
        #   (col 1's bin id, ..., col N's bin id)
        # and converts it to
        #   (col 1's val, ..., col N's val).
        self.column_bin_to_val_funcs = [c.BinToVal for c in columns]
        self.val_to_bin_funcs = [c.ValToBin for c in columns]

        self.name_to_index = {c.Name(): i for i, c in enumerate(self.columns)}

        if pg_name:
            self.pg_name = pg_name
        else:
            self.pg_name = name

    def __repr__(self):
        return '{}({})'.format(self.name, self.columns)

    def _validate_cardinality(self, columns):
        """Checks that all the columns have same the number of rows."""
        cards = [len(c.data) for c in columns]
        c = np.unique(cards)
        assert len(c) == 1, c
        return c[0]

    def to_df(self):
        return pd.DataFrame({c.name: c.data for c in self.columns})

    def Name(self):
        """Name of this table."""
        return self.name

    def Columns(self):
        """Return the list of Columns under this table."""
        return self.columns

    def ColumnIndex(self, name, allow_fail=True):
        """Returns index of column with the specified name."""
        if allow_fail:
            assert name in self.name_to_index, (name,
                                                list(self.name_to_index.keys()))
            return self.name_to_index[name]
        else:
            return self.name_to_index.get(name, None)

    def __getitem__(self, column_name):
        return self.columns[self.name_to_index[column_name]]

    def TableColumnIndex(self, source_table, col):
        """Returns index of column with the specified name/source."""
        name = JoinTableAndColumnNames(source_table, col)
        assert name in self.name_to_index, (name,
                                            list(self.name_to_index.keys()))
        return self.name_to_index[name]


class CsvTable(Table):

    def __init__(self,
                 name,
                 filename_or_df,
                 cols,
                 type_casts,
                 pre_add_noise=False,
                 pre_normalize=False,
                 post_normalize=False,
                 pg_name=None,
                 pg_cols=None,
                 dropna=False,
                 irr_attrs=[],
                 PK_tuples_np=None,
                 all_dvs=None,
                 **kwargs):
        """Accepts same arguments as pd.read_csv().

        Args:
            filename_or_df: pass in str to reload; otherwise accepts a loaded
              pd.Dataframe.
        """
        self.name = name
        self.pg_name = pg_name
        assert PK_tuples_np is not None
        self.PK_tuples_np = PK_tuples_np
        self.all_dvs = all_dvs

        if isinstance(filename_or_df, str):
            self.data = self._load(filename_or_df, cols, **kwargs)
        else:
            assert False
            assert isinstance(filename_or_df, pd.DataFrame)
            self.data = filename_or_df

        self.dropna = dropna
        if dropna:
            # NOTE: this might make the resulting dataframe much smaller.
            self.data = self.data.dropna()

        # from FactorJoin code
        for attr in irr_attrs:
            assert attr in self.data.columns
            self.data = self.data.drop(attr, axis=1)

        normalize = pre_normalize or post_normalize
        treat_as_numeric = normalize or pre_add_noise

        self.min = None
        self.max = None

        cols = self.data.columns
        self.columns = self._build_columns(self.data, cols, type_casts, pg_cols)

        if treat_as_numeric:
            for i, col in enumerate(self.columns):
                col.mean = self.mean[i] if normalize else None
                col.std  = self.std[i]  if normalize else None
                col.min  = self.min[i]
                col.max  = self.max[i]

        super(CsvTable, self).__init__(name, self.columns, pg_name)

    def _load(self, filename, cols, **kwargs):
        print('Loading csv...', end=' ')
        s = time.time()
        # table0
        table = filename.split('/')[-1].split('.')[0]
        # original name
        org_table = filename.split('/')[-2]
        if table in table_dtype.keys():
            dtype_dict = table_dtype[table]
        else:
            dtype_dict = dict()

        if cols:
            assert False
            df = pd.read_csv(filename, usecols=cols,dtype=dtype_dict,low_memory=False,keep_default_na=False,na_values=[''], **kwargs)
        else:
            df = pd.read_csv(filename, dtype=dtype_dict,low_memory=False,keep_default_na=False,na_values=[''], **kwargs)

        if len(df) == 0:
            conn = psycopg2.connect(database="stack", user="postgres", password="postgres", host="localhost", port=5432,)
            conn.set_client_encoding('UTF8')
            query = "select * from " + org_table + " ;"
            print(query)
            df_rows = pd.read_sql(query, conn)
            for col in df.columns.tolist():
                assert col in df_rows.columns.tolist(), f'{col} not in {df_rows.columns.tolist()}'
            df = df_rows[df.columns.tolist()]
            conn.close()

        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].str.strip()
        if cols is not None:
            df = df[cols]
        print('done, took {:.1f}s'.format(time.time() - s))
        return df

    def _build_columns(self, data, cols, type_casts, pg_cols):
        """Example args:

            cols = ['Model Year', 'Reg Valid Date', 'Reg Expiration Date']
            type_casts = {'Model Year': int}

        Returns: a list of Columns.
        """
        print('Parsing...', end=' ')
        s = time.time()
        for col, typ in type_casts.items():
            if col not in data:
                continue
            if typ != np.datetime64:
                data[col] = data[col].astype(typ, copy=False)
            else:
                data[col] = pd.to_datetime(data[col],
                                           infer_datetime_format=True,
                                           cache=True)

        # Discretize & create Columns.
        columns = []
        if pg_cols is None:
            pg_cols = [None] * len(cols)
        for c, p in zip(cols, pg_cols):
            col = Column(c, pg_name=p)
            col.Fill(data[c])

            if self.PK_tuples_np is not None and col.name in self.PK_tuples_np:
                col.SetDistribution(self.PK_tuples_np[col.name])
            elif self.all_dvs is not None and col.name in self.all_dvs:
                assert False
                # only used for data updates
                col.SetDistribution(self.all_dvs[col.name])
            else:
                if False:
                    print(f'{col.name} assertion failed')
                    assert self.PK_tuples_np is not None
                    print(f'{self.PK_tuples_np.keys()}')
                    assert self.all_dvs is not None
                    print(f'{self.all_dvs.keys()}')
                    assert False
                # non-key columns
                col.SetDistribution(data[c].value_counts(dropna=False).index.values)
            columns.append(col)
        print('done, took {:.1f}s'.format(time.time() - s))
        return columns


class FactorizedTable(Dataset):
    """Wraps a TableDataset to factorize large-card columns."""

    def __init__(self, table_dataset, word_size_bits=5, join_keys=[], compute_min_count=False, subvar_dropout=False, adjust_fact_col=False):
        assert isinstance(table_dataset, TableDataset), table_dataset
        self.table_dataset = table_dataset
        self.base_table = self.table_dataset.table
        self.word_size_bits = word_size_bits
        self.word_size = 2**self.word_size_bits

        self.join_keys = join_keys

        # use the table_dataset.table.columns' all_distinct_values
        self.columns, self.factorized_tuples_np = self._factorize(
            self.table_dataset.tuples_np,
            compute_min_count,
            subvar_dropout,
            adjust_fact_col)
        self.factorized_tuples = torch.as_tensor(
            self.factorized_tuples_np.astype(copy=False, dtype=np.float32))
        self.cardinality = table_dataset.table.cardinality

    def _factorize(self, tuples_np,
                   compute_min_count, subvar_dropout, adjust_fact_col):
        """Factorize K columns into N>K columns based on word size."""

        factorized_data = []
        cols = []
        if compute_min_count:
            self.min_count = dict()
            min_count_time = 0

        for i, col in enumerate(self.table_dataset.table.Columns()):
            use_PK_tuples_np = False
            assert not use_PK_tuples_np
            assert col.DistributionSize() == col.distribution_size
            dom = col.DistributionSize()
            if dom <= self.word_size:
                factorized_data.append(tuples_np[:, i])
                new_col = Column(col.name,
                                 distribution_size=dom)
                new_col.SetDistribution(col.all_distinct_values)
                cols.append(new_col)
            else:
                domain_bits = num_bits = len(bin(dom)) - 2
                word_mask = self.word_size - 1
                j = 0
                discretized_domain = np.arange(len(col.all_distinct_values))
                if compute_min_count:
                    dist_sizes = []

                while num_bits > 0:  # slice off the most significant bits
                    bit_width = min(num_bits, self.word_size_bits)
                    num_bits -= self.word_size_bits
                    temp_data = None
                    if num_bits < 0:
                        org_data = tuples_np[:, i] & (word_mask >> -num_bits)
                        new_data = discretized_domain & (word_mask >> -num_bits)
                        factorized_data.append(org_data)
                        dist_size = len(np.unique(new_data))
                        assert dist_size <= 2**(self.word_size_bits + num_bits)
                        if compute_min_count:
                            dist_sizes.append(dist_size)
                        f_col = Column(col.name + "_fact_" + str(j),
                                       distribution_size=1 if subvar_dropout and adjust_fact_col and col.name in self.join_keys
                                       else dist_size,
                                       factor_id=j,
                                       bit_width=bit_width,
                                       bit_offset=0,
                                       domain_bits=domain_bits,
                                       num_bits=num_bits)
                    else:
                        org_data = (tuples_np[:, i] >> num_bits) & word_mask
                        new_data = (discretized_domain >> num_bits) & word_mask
                        factorized_data.append(org_data)
                        dist_size = len(np.unique(new_data))
                        assert dist_size <= self.word_size
                        if compute_min_count:
                            dist_sizes.append(dist_size)
                        f_col = Column(col.name + "_fact_" + str(j),
                                       distribution_size=dist_size,
                                       factor_id=j,
                                       bit_width=bit_width,
                                       bit_offset=num_bits,
                                       domain_bits=domain_bits,
                                       num_bits=num_bits)

                    if subvar_dropout and adjust_fact_col and col.name in self.join_keys and j > 0:
                        f_col.SetDistribution(np.zeros(1))
                    else:
                        f_col.SetDistribution(new_data)
                    cols.append(f_col)
                    j += 1
                if compute_min_count:
                    assert len(dist_sizes) == 2
                    t1 = time.time()
                    all_count = np.zeros(dist_sizes)
                    np.add.at(all_count, (factorized_data[-2], factorized_data[-1]), 1)
                    min_count = np.sum(all_count, axis=1) / np.max(all_count, axis=1)
                    min_count[np.isnan(min_count)] = dist_sizes[-1]
                    self.min_count[col.name] = min_count
                    min_count_time += time.time() - t1
                if subvar_dropout and adjust_fact_col and col.name in self.join_keys:
                    factorized_data[-1] = factorized_data[-1] * 0.

        if compute_min_count:
            print('computing min_count time:', min_count_time)

        return cols, np.stack(factorized_data, axis=1)

    def size(self):
        return self.table_dataset.size()

    def __len__(self):
        return len(self.table_dataset)

    def __getitem__(self, idx):
        return self.factorized_tuples[idx]


class TableDataset(Dataset):
    """Wraps a Table and yields each row as a Dataset element."""

    def __init__(self, table, discretize=True, add_noise=False, input_encoding=None, rng=None, PK_tuples_np=None):
        """Wraps a Table.

        Args:
          table: the Table.
        """
        super(TableDataset, self).__init__()
        self.table = copy.deepcopy(table)
        assert PK_tuples_np is None

        print('Discretizing table...', end=' ')
        s = time.time()
        # [cardianlity, num cols].
        self.tuples_np = np.stack(
            [self.Discretize(c, discretize, PK_tuples_np) for c in self.table.Columns()], axis=1)

        self.tuples = torch.as_tensor(
            self.tuples_np.astype(np.float32, copy=False))
        print('done, took {:.1f}s'.format(time.time() - s))
        print('Discretized table', self.tuples)

        self.add_noise = add_noise

    def Discretize(self, col, discretize, PK_tuples_np=None):
        """Discretize values into its Column's bins.

        Args:
          col: the Column.
        Returns:
          col_data: discretized version; an np.ndarray of type np.int32.
        """
        return Discretize(col, discretize, PK_tuples_np=PK_tuples_np)

    def size(self):
        return len(self.tuples)

    def __len__(self):
        return len(self.tuples)

    def __getitem__(self, idx):
        if self.add_noise:
            noise = torch.rand_like(self.tuples[idx]) - 0.5
            return self.tuples[idx] + noise
        else:
            return self.tuples[idx]


def Discretize(col, discretize: bool, data=None, fail_out_of_domain=True, PK_tuples_np=None,
               use_val_to_bin=False):
    """Transforms data values into integers using a Column's vocab.

    Args:
        col: the Column.
        data: list-like data to be discretized.  If None, defaults to col.data.
        fail_out_of_domain: If True, then fail if we try to discretize
          out-of-domain data.  If False, then throw out out-of-domain data.
          Setting it to false is only safefor discretizing IN/equality
          literals and unsafe for other comparisons.

    Returns:
        col_data: discretized version; an np.ndarray of type np.int32.
    """

    assert PK_tuples_np is None

    if data is None:
        data = col.data

    if use_val_to_bin:
        hasnan = col.hasnan
    else:
        hasnan = pd.isnull(col.all_distinct_values).any()
    if hasnan:
        assert pd.isnull(col.all_distinct_values[0])
        if use_val_to_bin:
            bin_ids = np.array([col.val_to_bin[d] for d in data if d in col.val_to_bin])
            assert len(bin_ids) <= len(data), f'data = {data}, bin_ids = {bin_ids}'
        else:
            dvs = col.all_distinct_values[1:]
            bin_ids = pd.Categorical(data, categories=dvs).codes
            assert len(bin_ids) == len(data), f'data = {data}, bin_ids = {bin_ids}'
        if fail_out_of_domain:
            if not ((bin_ids[~pd.isnull(data)] >= 0).all() or ('_fanout' in col.name)):
                bin_ids = np.nan_to_num(bin_ids)
        if not use_val_to_bin:
            bin_ids = bin_ids + 1
    else:
        if discretize:
            if use_val_to_bin:
                bin_ids = np.array([col.val_to_bin[d] for d in data if d in col.val_to_bin])
                assert len(bin_ids) <= len(data), (len(bin_ids), len(data))
            else:
                dvs = col.all_distinct_values
                bin_ids = pd.Categorical(data, categories=dvs).codes
                assert len(bin_ids) == len(data), (len(bin_ids), len(data))
            #if fail_out_of_domain:
            #XXX when inc-movie_info
            if False:
                assert (bin_ids[~pd.isnull(data)] >= 0).all(), (col, data, bin_ids)
        else:
            assert False
            return data.astype(np.float32, copy=False)

    return bin_ids.astype(np.int32, copy=False)


class FactorizedSampleFromJoinIterDataset(IterableDataset):
    """Wraps a SampleFromJoinIterDataset to factorize large-card columns."""

    def __init__(self,
                 join_iter,
                 base_table,
                 factorize_blacklist=[],
                 word_size_bits=5,
                 factorize_fanouts=False):
        """Column factorization with join sampling.

        Args:
          join_iter: An instance of SampleFromJoinIterDataset class.
          base_table: The concatenated table representing the join.
          factorize_blacklist: Don't factorize these columns.
          word_size_bits: Maximum word bit size for factorized columns. Columns
            are factorized if len(col_dom) > 2**word_size_bits and not in
            blacklist. How much they are factorized by is specified in
            word_size_bits.
          factorize_fanouts: whether to factorize fanout columns.  If set to
            True, estimators must be modified to learn to draw a concrete
            fanout value from several subcolumns (or make sure that fanout is
            never used during inference).
        """
        assert isinstance(join_iter, SamplerBasedIterDataset), join_iter
        self.join_iter_dataset = join_iter
        self.word_size_bits = word_size_bits
        self.word_size = 2**self.word_size_bits
        self.factorize_fanouts = factorize_fanouts
        self.fact_col_mapping = defaultdict(
            list)  # Mapping from table col to fact cols.
        self.base_table = base_table
        self.base_table_cols = self.join_iter_dataset.columns_in_join()
        self.cardinality = self.base_table.cardinality
        self.factorize_blacklist = factorize_blacklist
        self.columns = self._factorize_columns()
        self.name_to_index = {c.Name(): i for i, c in enumerate(self.columns)}

    def __getitem__(self, column_name):
        return self.columns[self.name_to_index[column_name]]

    def _factorize_columns(self):
        assert False
        """Factorizes columns into subcolumns based on word size."""

        def _should_not_factorize(column):
            dom = column.distribution_size
            if dom <= self.word_size or column.name in self.factorize_blacklist:
                return True

            # By default, estimators.ProgressiveSampling._scale_probs()
            # assumes virtual columns are not factorized.  Flag
            # 'factorize_fanouts' is unsafe in general (unless inference is
            # modified to sample from factorized fanouts).
            if column.name.startswith('__in'):
                return True
            if column.name.startswith('__fanout'):
                return not self.factorize_fanouts

            return False

        cols = []
        self.combined_columns_types = []  # Column types for factorized columns.
        self.table_indexes = []  # Fact col index -> Table index.
        self.table_num_columns = [0] * len(
            self.join_iter_dataset.table_num_columns)
        for i, col in enumerate(self.base_table_cols):
            dom = col.DistributionSize()
            if _should_not_factorize(col):
                # Don't factorize this column.
                new_col = Column(col.name,
                                 distribution_size=col.distribution_size)
                new_col.SetDistribution(col.all_distinct_values)
                cols.append(new_col)
                self.combined_columns_types.append(
                    self.join_iter_dataset.combined_columns_types[i])
                self.table_indexes.append(
                    self.join_iter_dataset.table_indexes[i])
                if not col.name.startswith('__'):
                    # table_num_columns should count content columns only.
                    self.table_num_columns[
                        self.join_iter_dataset.table_indexes[i]] += 1
            else:
                domain_bits = num_bits = len(bin(dom)) - 2
                word_mask = self.word_size - 1
                j = 0
                col_dv = np.arange(dom)
                while num_bits > 0:
                    bit_width = min(num_bits, self.word_size_bits)
                    num_bits -= self.word_size_bits
                    if num_bits < 0:
                        fact_col_dv = col_dv & (word_mask >> -num_bits)
                        dist_size = len(np.unique(fact_col_dv))
                        assert dist_size <= 2**(self.word_size_bits + num_bits)
                        f_col = Column(col.name + '_fact_' + str(j),
                                       distribution_size=dist_size,
                                       factor_id=j,
                                       bit_width=bit_width,
                                       bit_offset=0,
                                       domain_bits=domain_bits,
                                       num_bits=num_bits)
                    else:
                        fact_col_dv = (col_dv >> num_bits) & word_mask
                        dist_size = len(np.unique(fact_col_dv))
                        assert dist_size <= self.word_size
                        f_col = Column(col.name + '_fact_' + str(j),
                                       distribution_size=dist_size,
                                       factor_id=j,
                                       bit_width=bit_width,
                                       bit_offset=num_bits,
                                       domain_bits=domain_bits,
                                       num_bits=num_bits)
                    f_col.SetDistribution(fact_col_dv)
                    cols.append(f_col)
                    self.fact_col_mapping[col].append(f_col)
                    self.combined_columns_types.append(
                        self.join_iter_dataset.combined_columns_types[i])
                    self.table_indexes.append(
                        self.join_iter_dataset.table_indexes[i])

                    if not col.name.startswith('__'):
                        # table_num_columns should count content columns only.
                        self.table_num_columns[
                            self.join_iter_dataset.table_indexes[i]] += 1
                    j += 1
        return cols

    def _factorize_data(self, data):
        word_mask = self.word_size - 1
        factorized_data = []
        for i, col in enumerate(self.base_table_cols):
            if col not in self.fact_col_mapping:
                # This column not factorized.
                factorized_data.append(data[:, i])
            else:
                # This column is factorized.
                for fact_col in self.fact_col_mapping[col]:
                    num_bits = fact_col.num_bits
                    if num_bits < 0:
                        fact_data = data[:, i] & (word_mask >> -num_bits)
                    else:
                        fact_data = (data[:, i] >> num_bits) & word_mask
                    factorized_data.append(fact_data)
        return np.stack(factorized_data, axis=1)

    def columns_in_join(self):
        return self.columns

    def ColumnIndex(self, name):
        assert name in self.name_to_index, (name,
                                            list(self.name_to_index.keys()))
        return self.name_to_index[name]

    def __iter__(self):
        return self

    def __next__(self):
        batch, i = self.join_iter_dataset.get_next()
        if i == 0:
            # This is a new batch. Need to factorize it.
            self.buffer = self._factorize_data(batch)
        return self.buffer[i]


class SamplerBasedIterDataset(IterableDataset):
    """A base class for sampler-based datasets."""

    def __init__(
            self,
            loaded_tables,
            join_spec,
            # +@ factorzied sampler
            rng,
            data_dir,
            dataset,
            use_cols,
            rust_random_seed,

            sample_batch_size=512,
            build_indexes=True,
            disambiguate_column_names=False,
            add_full_join_indicators=True,
            add_full_join_fanouts=True,
            initialize_sampler=True,
            indicator_one=False,
            # Experimental: save/load CSV.
            save_samples=None,
            load_samples=None,

            post_add_noise=False,
            post_normalize=False
    ):
        self.data_dir = data_dir
        self.dataset = dataset
        self.use_cols = use_cols
        self.rust_random_seed = rust_random_seed
        self.indicator_one = indicator_one

        self.join_spec = join_spec
        self.join_keys = join_spec.join_keys
        self.how = join_spec.join_how
        assert self.how in ['inner', 'outer'], join_spec
        self.tables = loaded_tables
        self.table_dict = {t.name: t for t in self.tables}
        self.dfs = [t.data for t in loaded_tables]
        self.disambiguate_column_names = disambiguate_column_names
        assert not (save_samples and load_samples), 'Set at most one of them.'
        self.save_samples = save_samples
        self.load_samples = load_samples

        self.post_add_noise = post_add_noise
        self.post_normalize = post_normalize

        self.buffer = None  # np.ndarray holding sampled tuples.
        self.sample_batch_size = sample_batch_size
        self.pointer = sample_batch_size

        self.add_full_join_indicators = add_full_join_indicators
        self.add_full_join_fanouts = add_full_join_fanouts

        # HACK: hard-code 'title' to be the primary relation.  As optimization
        # don't add virtual columns for this table.
        table_names = join_spec.join_tables

        # self.primary_table_index = table_names.index('title')
        self.primary_table_index = table_names.index(self.join_spec.join_root)

        self.combined_columns = []
        self.combined_columns_types = []
        self.table_indexes = []  # column index -> table index
        self.table_num_columns = [0] * len(
            self.tables)  # table index -> num normal attrs of that table

        join_pred = True
        if 'join_pred' in os.environ and os.environ['join_pred'] != 'True':
            print("Do not use join column to predication")
            join_pred = False

        for i, t in enumerate(self.tables):
            for c in t.columns:
                # Assume that there are no filters on join keys.
                # if c.name not in self.join_keys[t.name]:
                if join_pred:
                    self.combined_columns.append(c)
                    self.combined_columns_types.append(TYPE_NORMAL_ATTR)
                    self.table_indexes.append(i)
                    self.table_num_columns[i] += 1
                    if disambiguate_column_names:
                        c.name = JoinTableAndColumnNames(t.name, c.name)
                elif c.name not in self.join_keys[t.name]:
                    self.combined_columns.append(c)
                    self.combined_columns_types.append(TYPE_NORMAL_ATTR)
                    self.table_indexes.append(i)
                    self.table_num_columns[i] += 1
                    if disambiguate_column_names:
                        c.name = JoinTableAndColumnNames(t.name, c.name)

        self._maybe_add_full_join_virtual_columns(self.combined_columns,
                                                  self.combined_columns_types,
                                                  self.table_indexes)

        if self.how == 'outer':
            # Necessary for discretization.
            print(
                'Full outer join specified, inserting np.nan to all column domains'
            )
            for col in self.combined_columns:
                col.InsertNullInDomain()

        if disambiguate_column_names:
            self.join_keys_set = set(
                JoinTableAndColumnNames(t, c)
                for t, cs in self.join_keys.items()
                for c in cs)
        else:
            self.join_keys_set = set(
                c for cs in self.join_keys.values() for c in cs)

        # +@ set rng
        self.rng = rng

        if initialize_sampler:
            self._init_sampler()

        if self.load_samples:
            self.materialized_samples = pd.read_csv(self.load_samples)
            self.materialized_samples_ptr = 0


    @abstractmethod
    def _init_sampler(self):
        raise NotImplementedError

    @abstractmethod
    def _run_sampler(self):
        raise NotImplementedError

    def _add_virtual_column(self, i, table_name, key, columns, types,
                            table_indexes, table_df, single_key):
        column = Column('__fanout_{}'.format(table_name) if single_key else
                        '__fanout_{}__{}'.format(table_name, key))
        max_count = table_df.groupby(by=[key]).size().max()
        if 'distinct_fanout_col' in os.environ and os.environ['distinct_fanout_col'] == 'True':
            assert False
            col_data = table_df.groupby(by=[key]).size().unique()
            print(f"Use distinct value as fanout column - size {max_count+1} to {len(col_data)}" )
            column.SetDistribution(col_data)
        else:
            column.SetDistribution(np.arange(max_count + 1))
        columns.append(column)
        types.append(TYPE_FANOUT)
        table_indexes.append(i)

    def _maybe_add_full_join_virtual_columns(self, columns, types,
                                             table_indexes):
        if self.add_full_join_indicators:
            for i, t in enumerate(self.tables):
                columns.append(
                    Column('__in_{}'.format(t.name)).Fill(np.array(
                        [np.nan, 1.0]),
                                                          infer_dist=True))
                types.append(TYPE_INDICATOR)
                table_indexes.append(i)
        if self.add_full_join_fanouts:
            for i, table in enumerate(self.tables):
                if i == self.primary_table_index:
                    # Optimization: if there is a primary table of a schema
                    # (i.e., a primary join key), we don't have to add virtual
                    # columns for this table.  Its fanouts are all 1s, anyway.
                    continue
                join_keys = self.join_keys[table.name]
                table_df = self.table_dict[table.name].data
                table_df.index.name = None
                for key in join_keys:
                    self._add_virtual_column(i, table.name, key, columns, types,
                                             table_indexes, table_df,
                                             len(join_keys) == 1)

    def columns_in_join(self):
        return self.combined_columns

    def __iter__(self):
        return self

    def _maybe_save_samples(self, sampled_df):
        import filelock
        if self.save_samples is not None:
            with filelock.FileLock(self.save_samples + '.lock'):
                if not os.path.exists(self.save_samples):
                    sampled_df.to_csv(self.save_samples,
                                      mode='w',
                                      header=True,
                                      index=False)
                else:
                    sampled_df.to_csv(self.save_samples,
                                      mode='a',
                                      header=False,
                                      index=False)

    def _load_samples_chunk(self):
        print('loading')
        ptr = self.materialized_samples_ptr
        self.materialized_samples_ptr += self.sample_batch_size
        total = len(self.materialized_samples)
        return self.materialized_samples[ptr:min(total, self.
                                                 materialized_samples_ptr)]

    def _sample_batch(self, do_discretize=True):
        """Samples a raw pd.DataFrame; optionally discretize into np.ndarray."""
        if self.rng is None:
            wi = torch.utils.data.get_worker_info()
            if wi is not None:
                # Worker processes.
                self.rng = np.random.RandomState(wi.id)
            else:
                # Main process.  Used for test set eval only.
                self.rng = np.random.RandomState()

        if self.load_samples:
            sampled_df = self._load_samples_chunk()
        else:
            sampled_df = self._run_sampler()

        assert len(sampled_df.columns) == len(self.combined_columns), (len(
            sampled_df.columns), sampled_df.columns, len(
                self.combined_columns), self.combined_columns)

        self._maybe_save_samples(sampled_df)

        self.pointer = 0
        if do_discretize:
            discretized = []
            for i, (col_name, col) in enumerate(
                    zip(sampled_df.columns, self.combined_columns)):
                # Dropped join keys?
                # assert col_name not in self.join_keys_set

                # Just some extra checks.
                if not self.disambiguate_column_names:
                    assert col_name == col.name, (sampled_df.columns, col_name,
                                                  col.name)
                else:
                    assert col.name.endswith(col_name), (sampled_df.columns,
                                                         col_name, col.name)

                discretized_col_data = Discretize(col, True, sampled_df.iloc[:, i])
                discretized.append(discretized_col_data.reshape(-1, 1))

            self.buffer = np.hstack(discretized)
        else:
            self.buffer = sampled_df

    def get_next(self, do_discretize=True):
        if self.pointer >= self.sample_batch_size:
            self._sample_batch(do_discretize)
        curr_pointer = self.pointer
        self.pointer += 1
        return self.buffer, curr_pointer

    def __next__(self):
        batch, i = self.get_next()
        return batch[i]


class SampleFromJoinIterDataset(SamplerBasedIterDataset):
    """An IterableDataset that samples from a join on the fly."""

    def _init_sampler(self):
        pass

    def _run_sampler(self):
        raise NotImplementedError


def ConcatTables(tables,
                 join_keys,
                 disambiguate_column_names=False,
                 sample_from_join_dataset=None):
    """Makes a dummy Table to represent the schema of a join result."""
    cols_in_join = sample_from_join_dataset.columns_in_join()
    names = [t.name for t in tables]
    table = Table('-'.join(names), cols_in_join, validate_cardinality=False)
    table.table_names = names
    return table


def JoinTableAndColumnNames(table_name, column_name, sep=':'):
    return '{}{}{}'.format(table_name, sep, column_name)
