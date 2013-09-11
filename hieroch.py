import sys
import datetime, time
import cio
import model
from debug import DEBUG

class cli:

    def run(self):
        self.db = model.Database('hieroch.db')
        self.cio = cio.cio()
        self.cio.print_status(0, "Hieroch.")

        self.store_id  = None
        self.today  = datetime.date.today()
        self.origin_no = model.origin_by_name('offline')

        self.loop()

        self.db.save()

    def loop(self):
        while True:
            line = self.cio.read_line(0).strip()
            quit = False
            if DEBUG:
                quit = self.command(line)
            else:
                try:
                    quit = self.command(line)
                except cio.PreviousException:
                    pass
                except Exception as e:
                    self.cio.writeln(e)
            self.db.save()
            if quit:
                break

    def command(self, cmd):
        if len(cmd) == 0:
            return

        if   cmd == "s":
            self.set_store(1)
        elif cmd == "t":
            self.set_today(1)
        elif cmd == "o":
            self.set_origin(1)
        elif cmd == "p":
            self.add_package_price(1)
        elif cmd == "v":
            self.view_prices_for_product(1)
        elif cmd == "w":
            self.view_prices_for_package(1)
        elif cmd == "check":
            self.run_checks()
        elif cmd == "q":
            return True
        else:
            self.cio.print_error(0, "Unknown command.")

    def set_store(self, level):
        self.cio.print_status(level, "Setting the current store.")
        store = self.choose_store(level, new = True)
        self.store_id = store['id']
        return self.store_id

    def run_checks(self):
        return self.db.run_checks()

    def ensure_store(self, level):
        if self.store_id != None:
            return
        return self.set_store(level)

    def choose(self, level, items, format, new, previous):
        if len(items) == 0:
            return None
        if len(items) == 1:
            return items[0]

        for i in range(len(items)):
            self.cio.writeln(("%d. " % (i + 1)) + format(items[i]), level)
        while True:
            n = self.cio.read_integer(level, "Choose.", new = new, previous = previous)
            if n >= 1 and n <= len(items):
                return items[n - 1]

    def choose_record(self, level, question, add_function, fetch_function, format_function, null = False, new = False, previous = False):
        while True:
            try:
                pattern = self.cio.read_string(level, question, null = null, new = new, previous = previous)
                if pattern == None:
                    return None
                value = self.choose(level + 1, fetch_function(pattern), format_function, new = new, previous = previous)
                if value != None:
                    return value
            except cio.NewException:
                if new:
                    return add_function(level + 1)

    def choose_store(self, level, null = False, new = False, previous = False):
        store = self.choose_record(level, "~Store.", self.add_store, self.db.get_store_by_name, lambda r: r['name'], null = null, new = new, previous = previous)
        if store != None:
            self.cio.print_status(level, store['name'])
        return store

    def choose_product(self, level, null = False, new = False, previous = False):
        product = self.choose_record(level, "~Product name.", self.add_product, self.db.get_product_by_name, self.format_product, null = null, new = new, previous = previous)
        if product != None:
            self.cio.print_status(level, self.format_product(product))
        return product

    def choose_brand(self, level, null = False, new = False, previous = False):
        brand = self.choose_record(level, "~Brand name.", self.add_brand, self.db.get_brand_by_name, lambda r: r['name'], null = null, new = new, previous = previous)
        if brand != None:
            self.cio.print_status(level, brand['name'])
        return brand

    def format_package(self, package, product = None):
        if product == None:
            product = self.db.get_product_by_id(package['product_id'])

        s = product['name']
        if product['extra'] != "":
            s = s + " " + product['extra']
        if package['extra'] != "":
            s = s + " " + package['extra']
        if package['brand_id'] != 0:
            s = s + " " + self.db.get_brand_by_id(package['brand_id'])['name']
        s = s + " " + str(package['amount']) + " " +  model.unit_by_no(product['unit'])

        return s

    def format_product(self, product):
        s = product['name']
        if product['extra'] != "":
            s += " " + product['extra']
        return s

    def choose_package(self, level, null = False, new = False, previous = False):
        def fetch_packages(pattern):
            return self.db.get_package_by_barcode(pattern) + self.db.get_package_by_product_name(pattern)

        package = self.choose_record(level, "~Bar code/~Product name.", self.add_package, fetch_packages, self.format_package, null = null, new = new, previous = previous)
        if package != None:
            self.cio.print_status(level, self.format_package(package))
        return package

    def read_form(self, level, options):
        result = [None] * len(options)
        count = len(options)
        index = 0
        while index < count:
            value = None

            option = options[index]

            null = option.get('null',  False)
            new  = option.get('new',   False)

            question = option.get('question', None)
            if hasattr(question, '__call__'):
                question = question(result)

            try:
                if   option['type'] == 'function': value = option['function'](level, null = null, new = new,   previous = True)
                elif option['type'] == 'string':   value = self.cio.read_string (level, question, null = null, previous = True)
                elif option['type'] == 'barcode':  value = self.cio.read_barcode(level, question, null = null, previous = True)
                elif option['type'] == 'float':    value = self.cio.read_float  (level, question, null = null, previous = True)
                elif option['type'] == 'money':    value = self.cio.read_money  (level, question, null = null, previous = True)
                elif option['type'] == 'unit':     value = self.cio.read_unit   (level, question, null = null, previous = True)
                else:
                    raise Exception("Unknown type: %s." % (option['type'],))
            except cio.PreviousException:
                index = index - 1
                if index < 0:
                    index = 0
                continue

            result[index] = value
            index = index + 1

        return result

    def add_product(self, level):
        self.cio.print_status(level, "Adding a product.")
        options = []
        options.append({'type': 'string', 'question': "Product name."})
        options.append({'type': 'string', 'question': "Features.", 'null': True})
        options.append({'type': 'unit',   'question': "Measurement unit."})
        name, extra, unit = self.read_form(level, options)
        return self.db.insert_product(name, extra, unit)

    def add_brand(self, level):
        self.cio.print_status(level, "Adding a brand.")
        options = []
        options.append({'type': 'string', 'question': "Brand name."})
        name, = self.read_form(level, options)
        return self.db.insert_brand(name)

    def add_store(self, level):
        self.cio.print_status(level, "Adding a store.")
        options = []
        options.append({'type': 'string', 'question': "Store name."})
        name, = self.read_form(level, options)
        return self.db.insert_store(name)

    def add_package_price(self, level):
        self.cio.print_status(level, "Adding a package price.")
        self.ensure_store(level + 1)
        options = []
        options.append({'type': 'function', 'function': self.choose_package, 'new': True})
        options.append({'type': 'money',    'question': "Price."})
        package, price = self.read_form(level, options)
        price = self.db.insert_price(self.store_id, package['id'], price, self.today, self.origin_no)

        self.print_prices_for_package(package)

        return price

    def add_package(self, level):
        def amount_question(values):
            return "Amount (%s)." % (model.unit_by_no(values[0]['unit']))

        self.cio.print_status(level, "Adding a package.")
        options = []
        options.append({'type': 'function', 'function': self.choose_product,               'new': True})
        options.append({'type': 'function', 'function': self.choose_brand,   'null': True, 'new': True})
        options.append({'type': 'string',   'question': "Extra.",            'null': True})
        options.append({'type': 'barcode',  'question': "Bar code.",         'null': True})
        options.append({'type': 'float',    'question': amount_question,     'null': True})
        product, brand, extra, barcode, amount = self.read_form(level, options)
        return self.db.insert_package(product['id'], brand['id'] if brand else None, extra, amount, barcode)

    def set_origin(self, level):
        while True:
            origin_no = self.cio.read_integer(level, "Origin.")
            origin_name = model.origin_by_no(origin_no)
            if origin_name != None:
                self.origin_no = origin_no
                self.cio.print_status(level, "Origin of prices is: %s." % (origin_name,))
                return self.origin_no

    def set_today(self, level):
        self.today = self.cio.read_date(level, "Date.")
        self.cio.print_status(level, "Today is %s." % (self.today,))
        return self.today

    def print_prices_for_product(self, product_id):
        product  = self.db.get_product_by_id(product_id)
        packages = self.db.get_packages_by_product_id(product_id)
        for package in packages:
            self.print_prices_for_package(package, product)

    def print_prices_for_package(self, package, product = None):
        if product == None:
            product = self.db.get_product_by_id(package['product_id'])
        prices = self.db.get_prices_by_package(package['id'])

        self.cio.text_color(self.cio.ATTR_BRIGHT, self.cio.COLOR_BLUE, self.cio.COLOR_BLACK)
        self.cio.writeln(self.format_package(package))

        for price in prices:
            value     = price['price'] / 100.0
            rate      = value / package['amount']
            unit_spec = model.unit_by_no(product['unit'])

            if  unit_spec == 'g':
                unit_spec = 'kg'
                rate = rate * 1000
            elif unit_spec == 'ml':
                unit_spec = 'l'
                rate = rate * 1000
            elif unit_spec == 'm':
                unit_spec = 'km'
                rate = rate * 1000

            self.cio.text_color(self.cio.ATTR_RESET, self.cio.COLOR_GREEN, self.cio.COLOR_BLACK)
            self.cio.write("%.2f/%s\t" % (rate, unit_spec))

            self.cio.text_color(self.cio.ATTR_RESET, self.cio.COLOR_WHITE, self.cio.COLOR_BLACK)
            self.cio.write("%s\t" % (self.db.get_store_by_id(price['store_id'])['name'],))
            self.cio.write("%s\n" % (str(price['date']),))

    def view_prices_for_product(self, level):
        self.print_prices_for_product(self.choose_product(level)['id'])

    def view_prices_for_package(self, level):
        self.print_prices_for_package(self.choose_package(level))

cli().run()