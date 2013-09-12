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

    BRAND_COLUMNS   = ['id', 'name']
    STORE_COLUMNS   = ['id', 'name']
    PRODUCT_COLUMNS = ['id', 'name', 'extra', 'unit']
    PACKAGE_COLUMNS = ['id', 'product_id', 'brand_id', 'extra', 'amount', 'barcode']
    PRICE_COLUMNS   = ['id', 'store_id', 'package_id', 'price', 'date', 'origin']

    def make_object(self, columns, values):
        object = {}
        for i in range(len(columns)):
            object[columns[i]] = values[i]
        return object

    def insert_brand(self, name):
        self.cursor.execute('INSERT INTO brands(name) VALUES(?)', (name,))
        return self.make_object(self.BRAND_COLUMNS, [self.cursor.lastrowid, name])

    def insert_store(self, name):
        self.cursor.execute('INSERT INTO stores(name) VALUES(?)', (name,))
        return self.make_object(self.STORE_COLUMNS, [self.cursor.lastrowid, name])

    def insert_product(self, name, extra, unit_no):
        if extra == None:
            extra = ""
        self.cursor.execute('INSERT INTO products(name, extra, unit) VALUES(?, ?, ?)', (name, extra, unit_no))
        return self.make_object(self.PRODUCT_COLUMNS, [self.cursor.lastrowid, name, extra, unit_no])

    def insert_package(self, product_id, brand_id, extra, amount, barcode):
        if extra == None:
            extra = ""
        if brand_id == None:
            brand_id = 0
        if amount == None:
            amount = 1
        self.cursor.execute('INSERT INTO packages(product_id, brand_id, extra, amount, barcode) VALUES(?, ?, ?, ?, ?)', (product_id, brand_id, extra, amount, barcode))
        return self.make_object(self.PACKAGE_COLUMNS, [self.cursor.lastrowid, product_id, brand_id, extra, amount, barcode])

    def insert_price(self, store_id, package_id, price, date, origin_no):
        self.cursor.execute('INSERT INTO prices(store_id, package_id, price, date, origin) VALUES(?, ?, ?, ?, ?)', (store_id, package_id, price, date, origin_no))
        return self.make_object(self.PRICE_COLUMNS, [self.cursor.lastrowid, store_id, package_id, price, date, origin_no])

    def get_brand_by_name(self, pattern):
        rows = self.cursor.execute('SELECT id, name FROM brands WHERE name LIKE ?', ("%%%s%%" % pattern,)).fetchall()
        return [self.make_object(self.BRAND_COLUMNS, row) for row in rows]

    def get_brand_by_id(self, id):
        row = self.cursor.execute('SELECT id, name FROM brands WHERE id = ?', (id,)).fetchall()[0]
        return self.make_object(self.BRAND_COLUMNS, row)

    def get_store_by_name(self, pattern):
        rows = self.cursor.execute('SELECT id, name FROM stores WHERE name LIKE ?', ("%%%s%%" % pattern,)).fetchall()
        return [self.make_object(self.STORE_COLUMNS, row) for row in rows]

    def get_store_by_id(self, id):
        row = self.cursor.execute('SELECT id, name FROM stores WHERE id = ?', (id,)).fetchall()[0]
        return self.make_object(self.STORE_COLUMNS, row)

    def get_product_by_name(self, pattern):
        rows = self.cursor.execute('SELECT id, name, extra, unit FROM products WHERE name LIKE ?', ("%%%s%%" % pattern,)).fetchall()
        return [self.make_object(self.PRODUCT_COLUMNS, row) for row in rows]

    def get_product_by_id(self, id):
        row = self.cursor.execute('SELECT id, name, extra, unit FROM products WHERE id = ?', (id,)).fetchall()[0]
        return self.make_object(self.PRODUCT_COLUMNS, row)

    def get_package_by_barcode(self, pattern):
        rows = self.cursor.execute('SELECT id, product_id, brand_id, extra, amount, barcode FROM packages WHERE barcode LIKE ?', ('%%%s%%' % pattern,)).fetchall()
        return [self.make_object(self.PACKAGE_COLUMNS, row) for row in rows]

    def get_package_by_product_name(self, pattern):
        rows = self.cursor.execute('SELECT packages.id, packages.product_id, packages.brand_id, packages.extra, packages.amount, packages.barcode FROM packages JOIN products ON packages.product_id = products.id WHERE products.name LIKE ?', ('%%%s%%' % pattern,)).fetchall()
        return [self.make_object(self.PACKAGE_COLUMNS, row) for row in rows]

    def get_packages_by_product_id(self, product_id):
        rows = self.cursor.execute('SELECT packages.id, packages.product_id, packages.brand_id, packages.extra, packages.amount, packages.barcode FROM packages JOIN products ON packages.product_id = products.id WHERE products.id = ?', (product_id,)).fetchall()
        return [self.make_object(self.PACKAGE_COLUMNS, row) for row in rows]

    def get_packages(self):
        rows = self.cursor.execute('SELECT id, product_id, brand_id, extra, amount, barcode FROM packages').fetchall()
        return [self.make_object(self.PACKAGE_COLUMNS, row) for row in rows]

    def get_prices_by_package(self, package_id):
        rows = self.cursor.execute('SELECT prices.id, prices.store_id, prices.package_id, prices.price, prices.date, prices.origin FROM prices JOIN packages ON prices.package_id = packages.id WHERE prices.package_id = ? ORDER BY date', (package_id,)).fetchall()
        rows = [self.make_object(self.PRICE_COLUMNS, row) for row in rows]
        for row in rows:
            s = row['date']
            row['date'] = datetime.date(int(s[0:4]), int(s[5:7]), int(s[8:10]))
        return rows

    def get_prices_with_filter(self, filter_specs = None):

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
                        pro.id AS product_id
                 FROM (((prices pri JOIN packages pac ON pri.package_id = pac.id)
                                    JOIN products pro ON pac.product_id = pro.id)
                                    JOIN brands bra ON pac.brand_id = bra.id)
                                    JOIN stores sto ON pri.store_id = sto.id
                 WHERE %s
                 ORDER BY pri.date, pri.price / pac.amount DESC
              """ % (where,)
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
                 'product_id':      row[12]}
                for row in rows]
        for row in rows:
            s = row['date']
            row['date'] = datetime.date(int(s[0:4]), int(s[5:7]), int(s[8:10]))
        return rows

    def run_checks(self):
        packages = self.get_packages()
        for package in packages:
            if package['barcode']:
                if not is_barcode_valid(package['barcode']):
                    self.cio.writeln("Invalid barcode for package %d: %s" % (package['id'], package['barcode']))
