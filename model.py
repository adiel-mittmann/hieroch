import _sqlite3 as sqlite3
import datetime, time

def adapt_date(date):
    return date.isoformat()

def is_barcode_valid(barcode):
    return check_digit(barcode[0:-1]) == barcode[-1]

def check_digit(codes):
    weights = [3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3, 1, 3]
    s = 0
    for i in range(len(codes)):
        s = s + weights[len(weights) - len(codes) + i] * int(codes[i])
    s = s % 10
    s = 10 - s
    if s == 10:
        s = 0
    return str(s)

def unit_by_name(name):
    try:
        return {"kg": 1, "g": 2, "l": 3, "ml": 4, "u": 5, "m": 6, "m2": 7}[name]
    except:
        return None

def unit_by_no(no):
    if no < 1:
        return None
    try:
        return ['kg', 'g', 'L', 'ml', 'u', 'm', "m2"][no - 1]
    except:
        return None

def origin_by_name(name):
    try:
        return {'offline': 1, 'website': 2}[name]
    except:
        return None

def origin_by_no(no):
    if no < 1:
        return None
    try:
        return ['offline', 'website'][no - 1]
    except:
        return None

class Database:

    def __init__(self, database_path):
        sqlite3.register_adapter(datetime.date, adapt_date)
        self.database_path = database_path
        self.db = sqlite3.connect(self.database_path)
        self.db.text_factory = str
        self.cursor = self.db.cursor()
        self.cursor.execute('PRAGMA foreign_keys = ON')

    def save(self):
        self.db.commit()

    BRAND_COLUMNS   = ['id', 'hide', 'name']
    STORE_COLUMNS   = ['id', 'hide', 'name']
    PRODUCT_COLUMNS = ['id', 'hide', 'name', 'extra', 'unit']
    PACKAGE_COLUMNS = ['id', 'hide', 'product_id', 'brand_id', 'extra', 'amount', 'barcode']
    PRICE_COLUMNS   = ['id', 'hide', 'store_id', 'package_id', 'price', 'date', 'origin', 'sic']

    def make_object(self, columns, values):
        object = {}
        for i in range(len(columns)):
            object[columns[i]] = values[i]
        return object

    def make_column_list(self, columns, prefix = None):
        s = ""
        for column in columns:
            if s != "":
                s += ", "
            if prefix != None:
                s += prefix + "."
            s += column
        return s

    def placeholders(self, count):
        return ', '.join((['?'] * count))

    def generic_insert(self, table, columns, values):
        some_columns = columns[:]
        some_columns.remove("id")
        some_columns.remove("hide")
        sql = 'INSERT INTO {0}({1}) VALUES({2})'.format(table, self.make_column_list(some_columns), self.placeholders(len(values)))
        self.cursor.execute(sql, values)
        return self.make_object(columns, [self.cursor.lastrowid, 0] + list(values))

    def generic_select(self, table, columns, values = (), suffix = None, first = False):
        if suffix == None:
            suffix = ""
        sql = 'SELECT {0} FROM {1} {2}'.format(self.make_column_list(columns), table, suffix)
        rows = self.cursor.execute(sql, values).fetchall()
        if first:
            return self.make_object(columns, rows[0])
        else:
            return [self.make_object(columns, row) for row in rows]

    def generic_get_by_id(self, table, columns, id):
        return self.generic_select(table, columns, suffix = "WHERE id = ?", values = (id,), first = True)

    def generic_get_recent(self, table, columns, count):
        return self.generic_select(table, columns, suffix = "ORDER BY id DESC LIMIT ?", values = (count,))

    def generic_get_hidden(self, table, columns):
        return self.generic_select(table, columns, suffix = "WHERE hide = 1")

    def generic_delete(self, table, id):
        self.cursor.execute('DELETE FROM ' + table + ' WHERE id = ?', (id,))

    def generic_toggle_hide_store(self, table, id):
        self.cursor.execute('UPDATE ' + table + ' SET hide = 1 - hide WHERE id = ?', (id,))

    def insert_brand(self, name):
        return self.generic_insert('brands', self.BRAND_COLUMNS, (name,))

    def insert_store(self, name):
        return self.generic_insert('stores', self.STORE_COLUMNS, (name,))

    def insert_product(self, name, extra, unit_no):
        if extra == None:
            extra = ""
        return self.generic_insert('products', self.PRODUCT_COLUMNS, (name, extra, unit_no))

    def insert_package(self, product_id, brand_id, extra, amount, barcode):
        if extra == None:
            extra = ""
        if brand_id == None:
            brand_id = 0
        if amount == None:
            amount = 1
        return self.generic_insert('packages', self.PACKAGE_COLUMNS, (product_id, brand_id, extra, amount, barcode))

    def insert_price(self, store_id, package_id, price, date, origin_no):
        return self.generic_insert('prices', self.PRICE_COLUMNS, (store_id, package_id, price, date, origin_no, None))

    def get_package_by_product_name_or_extra(self, pattern):
        rows = self.cursor.execute('SELECT ' + self.make_column_list(self.PACKAGE_COLUMNS, 'packages') + ' FROM (packages JOIN products ON packages.product_id = products.id) JOIN prices ON packages.id = prices.package_id WHERE (products.name LIKE ?) OR (products.extra LIKE ?) GROUP BY packages.id ORDER BY COUNT(prices.id) DESC', ('%%%s%%' % pattern, '%%%s%%' % pattern)).fetchall()
        return [self.make_object(self.PACKAGE_COLUMNS, row) for row in rows]

    def get_packages_by_product_id(self, product_id):
        rows = self.cursor.execute('SELECT ' + self.make_column_list(self.PACKAGE_COLUMNS, 'packages') + ' FROM packages JOIN products ON packages.product_id = products.id WHERE products.id = ?', (product_id,)).fetchall()
        return [self.make_object(self.PACKAGE_COLUMNS, row) for row in rows]

    def get_prices_by_package(self, package_id):
        rows = self.cursor.execute('SELECT ' + self.make_column_list(self.PRICE_COLUMNS, 'prices') + ' FROM prices JOIN packages ON prices.package_id = packages.id WHERE prices.package_id = ? ORDER BY date', (package_id,)).fetchall()
        rows = [self.make_object(self.PRICE_COLUMNS, row) for row in rows]
        for row in rows:
            s = row['date']
            row['date'] = datetime.date(int(s[0:4]), int(s[5:7]), int(s[8:10]))
        return rows

    def get_prices_with_filter(self, filter_specs = None, order = None, limit = None):

        where  = "1"
        params = []
        if filter_specs != None:
            for filter_spec in filter_specs:
                if filter_spec['match'] == 'fuzzy':
                    where += " AND " + filter_spec['field'] + " LIKE ?"
                    params.append("%" + filter_spec['value'] + "%")
                else:
                    where += " AND " + filter_spec['field'] + " = ?"
                    params.append(filter_spec['value'])

        if order != None:
            if order == "id":
                order = "ORDER BY id DESC"
        else:
            order = "ORDER BY pri.date, pri.price / pac.amount DESC"

        if limit != None:
            limit = "LIMIT {0}".format(limit)
        else:
            limit = ""

        sql = """SELECT pro.name AS product_name,
                        pro.extra AS product_extra,
                        pro.unit AS product_unit,
                        bra.name AS brand_name,
                        pac.extra AS package_extra,
                        pac.amount AS package_amount,
                        pac.barcode AS package_barcode,
                        sto.name AS store_name,
                        pri.price AS price,
                        pri.date AS date,
                        pri.id AS id,
                        pac.id AS package_id,
                        pro.id AS product_id,
                        pri.sic AS sic
                 FROM (((prices pri JOIN packages pac ON pri.package_id = pac.id)
                                    JOIN products pro ON pac.product_id = pro.id)
                                    JOIN brands bra ON pac.brand_id = bra.id)
                                    JOIN stores sto ON pri.store_id = sto.id
                 WHERE %s
                 AND pri.hide = 0 AND pac.hide = 0 AND pro.hide = 0 AND bra.hide = 0 AND sto.hide = 0
                 %s
                 %s
              """ % (where, order, limit)
        rows = self.cursor.execute(sql, params)

        rows = [{'product_name':    row[0],
                 'product_extra':   row[1],
                 'product_unit':    row[2],
                 'brand_name':      row[3],
                 'package_extra':   row[4],
                 'package_amount':  row[5],
                 'package_barcode': row[6],
                 'store_name':      row[7],
                 'price':           row[8],
                 'date':            row[9],
                 'id':              row[10],
                 'package_id':      row[11],
                 'product_id':      row[12],
                 'sic':             row[13]}
                for row in rows]
        for row in rows:
            s = row['date']
            row['date'] = datetime.date(int(s[0:4]), int(s[5:7]), int(s[8:10]))
        return rows

    def get_brand_by_name(self, pattern):
        return self.generic_select('brands', self.BRAND_COLUMNS, suffix = "WHERE name LIKE ?", values = ("%%%s%%" % pattern,))

    def get_store_by_name(self, pattern):
        return self.generic_select('stores', self.STORE_COLUMNS, suffix = "WHERE name LIKE ?", values = ("%%%s%%" % pattern,))

    def get_product_by_name(self, pattern):
        return self.generic_select('products', self.PRODUCT_COLUMNS, suffix = "WHERE name LIKE ?", values = ("%%%s%%" % pattern,))

    def get_package_by_barcode(self, pattern):
        return self.generic_select('packages', self.PACKAGE_COLUMNS, suffix = "WHERE barcode LIKE ?", values = ('%%%s%%' % pattern,))

    def get_brand_by_id(self, id):
        return self.generic_get_by_id('brands', self.BRAND_COLUMNS, id)

    def get_store_by_id(self, id):
        return self.generic_get_by_id('stores', self.STORE_COLUMNS, id)

    def get_product_by_id(self, id):
        return self.generic_get_by_id('products', self.PRODUCT_COLUMNS, id)

    def get_package_by_id(self, id):
        return self.generic_get_by_id('packages', self.PACKAGE_COLUMNS, id)

    def get_recent_brands(self, count):
        return self.generic_get_recent('brands', self.BRAND_COLUMNS, count)

    def get_recent_stores(self, count):
        return self.generic_get_recent('stores', self.STORE_COLUMNS, count)

    def get_recent_products(self, count):
        return self.generic_get_recent('products', self.PRODUCT_COLUMNS, count)

    def get_recent_packages(self, count):
        return self.generic_get_recent('packages', self.PACKAGE_COLUMNS, count)

    def get_hidden_brands(self):
        return self.generic_get_hidden('brands', self.BRAND_COLUMNS)

    def get_hidden_stores(self):
        return self.generic_get_hidden('stores', self.STORE_COLUMNS)

    def get_hidden_products(self):
        return self.generic_get_hidden('products', self.PRODUCT_COLUMNS)

    def get_hidden_packages(self):
        return self.generic_get_hidden('packages', self.PACKAGE_COLUMNS)

    def get_all_packages(self):
        return self.generic_select('packages', self.PACKAGE_COLUMNS)

    def get_all_prices(self):
        return self.generic_select('prices', self.PRICE_COLUMNS)

    def delete_price(self, id):
        self.generic_delete('prices', id)

    def delete_package(self, id):
        self.generic_delete('packages', id)

    def delete_product(self, id):
        self.generic_delete('products', id)

    def delete_store(self, id):
        self.generic_delete('stores', id)

    def delete_brand(self, id):
        self.generic_delete('brands', id)

    def toggle_hide_store(self, id):
        self.generic_toggle_hide_store('stores', id)

    def toggle_hide_brand(self, id):
        self.generic_toggle_hide_store('brands', id)

    def toggle_hide_package(self, id):
        self.generic_toggle_hide_store('packages', id)

    def toggle_hide_product(self, id):
        self.generic_toggle_hide_store('products', id)

