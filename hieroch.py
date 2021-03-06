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
                    self.cio.writeln(str(e))
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
        elif cmd == "w":
            self.view_prices_for_package(1)
        elif cmd == "x":
            self.view_prices(1)
        elif cmd == "ds":
            self.delete_last_store(1)
        elif cmd == "db":
            self.delete_last_brand(1)
        elif cmd == "dr":
            self.delete_last_product(1)
        elif cmd == "dp":
            self.delete_last_package(1)
        elif cmd == "dc":
            self.delete_last_price(1)
        elif cmd == "vhs":
            self.view_hidden_stores(1)
        elif cmd == "vhb":
            self.view_hidden_brands(1)
        elif cmd == "vhr":
            self.view_hidden_products(1)
        elif cmd == "vhp":
            self.view_hidden_packages(1)
        elif cmd == "hs":
            self.hide_store(1)
        elif cmd == "hb":
            self.hide_brand(1)
        elif cmd == "hp":
            self.hide_package(1)
        elif cmd == "hr":
            self.hide_product(1)
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

        def multiply(s, package_unit):
            s = s + " "
            i = 0
            a = 0
            nums = []
            snum = ""
            sunit = ""
            while i < len(s):
                c = s[i]
                if   a == 0:
                    if   c >= '0' and c <= '9':
                        snum = c
                        sunit = ""
                        a = 1
                elif a == 1:
                    if   c == " ":
                        nums.append([snum, sunit])
                        a = 2
                    else:
                        if (c >= '0' and c <= '9') or c == '.':
                            snum += c
                        else:
                            sunit += c
                elif a == 2:
                    if   c == " ":
                        a = 0
                i += 1
            if len(nums) > 1:
                value = 1.0
                for num, unit in nums:
                    if   unit == "u" or unit == package_unit or (unit + "2") == package_unit:
                        value *= float(num)
                    elif unit == "cm" and (package_unit == "m" or package_unit == "m2"):
                        value *= float(num) / 100.0
                    else:
                        raise Exception("Don't know what to do with units: %s and %s." % (unit, package_unit))
                return value
            else:
                return None

        packages = self.db.get_all_packages()
        for package in packages:
            if package['barcode']:
                if not model.is_barcode_valid(package['barcode']):
                    self.cio.writeln("Invalid barcode for package %d: %s" % (package['id'], package['barcode']))

        packages = self.db.get_all_packages()
        for package in packages:
            unit = model.unit_by_no(self.db.get_product_by_id(package['product_id'])['unit'])
            value = multiply(package['extra'], unit)
            if value != None:
                if value != package['amount']:
                    self.cio.writeln("Suspect amount:")
                    self.cio.writeln(self.format_package(package, verbose = True))

        prices = self.db.get_all_prices()
        for i in range(len(prices)):
            if prices[i]['sic'] == 1:
                continue
            if i > 0:
                same = ['origin', 'store_id', 'price', 'package_id', 'date']
                count = 0
                for attr in same:
                    if prices[i][attr] == prices[i - 1][attr]:
                        count += 1
                if count > 3:
                    self.cio.writeln("{0} // {1}".format(prices[i - 1]['id'], prices[i]['id']))
                    for attr in same:
                        if prices[i][attr] != prices[i - 1][attr]:
                            if attr == 'package_id':
                                pkg1 = self.db.get_package_by_id(prices[i - 1]['package_id'])
                                pkg2 = self.db.get_package_by_id(prices[i    ]['package_id'])
                                self.cio.writeln("package:")
                                self.cio.writeln("        " + self.format_package(pkg1, verbose = True))
                                self.cio.writeln("        --")
                                self.cio.writeln("        " + self.format_package(pkg2, verbose = True))
                            else:
                                pkg = self.db.get_package_by_id(prices[i]['package_id'])
                                self.cio.writeln("        " + self.format_package(pkg, verbose = True))
                                self.cio.writeln("{0}: {1} -- {2}".format(attr, prices[i - 1][attr], prices[i][attr]))

    def ensure_store(self, level):
        if self.store_id != None:
            return
        return self.set_store(level)

    def choose(self, level, items, format, new, previous):
        if len(items) == 0:
            return None
        if len(items) == 1:
            return items[0]

        for i in reversed(range(len(items))):
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

    def format_package(self, package, product = None, verbose = False):
        if product == None:
            product = self.db.get_product_by_id(package['product_id'])

        brand_name = ""
        if package['brand_id'] != 0:
            brand_name = self.db.get_brand_by_id(package['brand_id'])['name']

        if verbose:
            return self.format_package_raw(product['name'], product['extra'], package['extra'], brand_name, package['amount'], product['unit'], package['id'], product['id'], package['barcode'])
        else:
            return self.format_package_raw(product['name'], product['extra'], package['extra'], brand_name, package['amount'], product['unit'])

    def format_package_raw(self, product_name, product_extra, package_extra, brand_name, package_amount, product_unit, package_id = None, product_id = None, package_barcode = None):
        s = product_name
        if product_id != None:
            s += " (" + str(product_id) + ")"
        if product_extra != "":
            s = s + " " + product_extra
        if package_extra != "":
            s = s + " " + package_extra
        if brand_name != "":
            s = s + " " + brand_name
        s = s + " " + str(package_amount) + "" +  model.unit_by_no(product_unit)
        if package_id != None:
            s += " (" + str(package_id) + ")"
        if package_barcode != None:
            s += " -- " + str(package_barcode)

        return s


    def format_product(self, product):
        s = product['name']
        if product['extra'] != "":
            s += " " + product['extra']
        return s

    def choose_package(self, level, null = False, new = False, previous = False):
        def fetch_packages(pattern):
            return self.db.get_package_by_barcode(pattern) + self.db.get_package_by_product_name_or_extra(pattern)

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

        filter_specs = [{'field': 'product_id', 'match': 'exact', 'value': package['product_id']}]
        prices = self.db.get_prices_with_filter(filter_specs)
        self.print_best_price_summary(prices, price['id'])

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

    def format_price(self, price, multiline = False):
        s = ""

        rate = price['price'] / 100.0 / price['package_amount']
        unit_spec = model.unit_by_no(price['product_unit'])
        if  unit_spec == 'g':
            unit_spec = 'kg'
            rate = rate * 1000
        elif unit_spec == 'ml':
            unit_spec = 'l'
            rate = rate * 1000
        elif unit_spec == 'm':
            unit_spec = 'km'
            rate = rate * 1000
        rate = "{0:03.2f}/{1}".format(rate, unit_spec)
        spec = self.format_package_raw(price['product_name'], price['product_extra'], price['package_extra'], price['brand_name'], price['package_amount'], price['product_unit'])

        ago = (datetime.date.today() - price['date']).days
        if   ago <= 90:
            ago = "{0:>2}d".format(ago)
        elif ago <= (36 * 30):
            ago = "{0:2.0f}m".format(ago / 30.0)
        else:
            ago = "{0:2.0f}y".format(ago / 365.0)

        discarded_count = 0
        if price.has_key('discarded_count'):
            discarded_count = price['discarded_count']
        if   discarded_count == 0:
            discarded_count = "  "
        elif discarded_count < 99:
            discarded_count = "{0:>2}".format(discarded_count)
        else:
            discarded_count = "++"

        store_name = price['store_name'][0:3]

        s += "{0} {1:>8} {2} {3:<3} ".format(discarded_count, rate, ago, store_name)
        if not multiline:
            s += spec
            return s

        cols = self.cio.columns()
        len_s = cio.utf8_len(s)
        len_spec = cio.utf8_len(spec)
        if (len_s >= cols) or (len_s + len_spec <= cols):
            s += spec
        else:
            left = len_s
            rem = cols - len_s
            first = True
            while cio.utf8_len(spec) > 0:
                if not first:
                    s += "\n" + (" " * left)
                first = False
                trunc, spec = cio.utf8_break(spec, rem)
                s += trunc
        return s

    def print_price(self, price, multiline = False):
        if   'highlight' in price:
            self.cio.text_color(self.cio.ATTR_BRIGHT, self.cio.COLOR_BLUE, self.cio.COLOR_BLACK)
        elif 'good' in price:
            self.cio.text_color(self.cio.ATTR_BRIGHT, self.cio.COLOR_CYAN, self.cio.COLOR_BLACK)
        elif 'price' in price:
            self.cio.text_color(self.cio.ATTR_BRIGHT, self.cio.COLOR_GREEN, self.cio.COLOR_BLACK)
        self.cio.write(self.format_price(price, multiline))
        self.cio.text_color(self.cio.ATTR_RESET, self.cio.COLOR_WHITE, self.cio.COLOR_BLACK)
        self.cio.write("\n")

    def print_best_price_summary(self, prices, highlight_id = None):
        minimum = float("inf")
        selected = []
        packages = set()
        for price in reversed(prices):
            rate = price['price'] / 100.0 / price['package_amount']
            append = False
            if rate < minimum:
                append = True
                minimum = rate
                price['good'] = True
            elif price['id'] == highlight_id:
                price['highlight'] = True
                append = True
            elif price['package_id'] not in packages:
                append = True
            packages.add(price['package_id'])
            if append:
                price['discarded_count'] = 0
                selected.append(price)
            else:
                selected[-1]['discarded_count'] += 1

        for price in reversed(selected):
            self.print_price(price, multiline = True)

    def view_prices_for_package(self, level):
        package = self.choose_package(level)
        filter_specs = [{'field': 'package_id', 'match': 'exact', 'value': package['id']}]
        prices = self.db.get_prices_with_filter(filter_specs)
        self.print_best_price_summary(prices)

    def view_prices(self, level):
        self.cio.print_status(level, "Checking prices.")
        options = []
        options.append({'type': 'string', 'question': "~Product name.",  'null': True})
        options.append({'type': 'string', 'question': "~Product extra.", 'null': True})
        options.append({'type': 'string', 'question': "~Package extra.", 'null': True})
        options.append({'type': 'string', 'question': "~Brand name.",   'null': True})
        fields = ['product_name', 'product_extra', 'package_extra', 'brand_name']
        values = self.read_form(level, options)
        filter_specs = []
        for i in range(len(fields)):
            if values[i] != None:
                filter_specs.append({'field': fields[i], 'match': 'fuzzy', 'value': values[i]})

        prices = self.db.get_prices_with_filter(filter_specs)
        self.print_best_price_summary(prices)

    def delete_last_store(self, level):
        rows = self.db.get_recent_stores(10)
        row = self.choose(level, rows, lambda r: r['name'], False, False)
        self.db.delete_store(row['id'])

    def delete_last_brand(self, level):
        rows = self.db.get_recent_brands(10)
        row = self.choose(level, rows, lambda r: r['name'], False, False)
        self.db.delete_brand(row['id'])

    def delete_last_product(self, level):
        rows = self.db.get_recent_products(10)
        row = self.choose(level, rows, self.format_product, False, False)
        self.db.delete_product(row['id'])

    def delete_last_package(self, level):
        rows = self.db.get_recent_packages(10)
        row = self.choose(level, rows, self.format_package, False, False)
        self.db.delete_package(row['id'])

    def delete_last_price(self, level):
        rows = self.db.get_prices_with_filter(None, "id", 10)
        row = self.choose(level, rows, self.format_price, False, False)
        self.db.delete_price(row['id'])

    def hide_store(self, level):
        self.cio.print_status(level, "Hiding/unhiding store.")
        store = self.choose_store(level, new = False)
        self.db.toggle_hide_store(store['id'])

    def hide_brand(self, level):
        self.cio.print_status(level, "Hiding/unhiding brand.")
        brand = self.choose_brand(level, new = False)
        self.db.toggle_hide_brand(brand['id'])

    def hide_package(self, level):
        self.cio.print_status(level, "Hiding/unhiding package.")
        package = self.choose_package(level, new = False)
        self.db.toggle_hide_package(package['id'])
        
    def hide_product(self, level):
        self.cio.print_status(level, "Hiding/unhiding product.")
        product = self.choose_product(level, new = False)
        self.db.toggle_hide_product(product['id'])

    def view_hidden_stores(self, level):
        self.cio.print_status(level, "Viewing hidden stores.")
        rows = self.db.get_hidden_stores()
        for row in rows:
            self.cio.writeln(row['name'], level)

    def view_hidden_brands(self, level):
        self.cio.print_status(level, "Viewing hidden brands.")
        rows = self.db.get_hidden_brands()
        for row in rows:
            self.cio.writeln(row['name'], level)

    def view_hidden_products(self, level):
        self.cio.print_status(level, "Viewing hidden products.")
        rows = self.db.get_hidden_products()
        for row in rows:
            self.cio.writeln(self.format_product(row), level)

    def view_hidden_packages(self, level):
        self.cio.print_status(level, "Viewing hidden packages.")
        rows = self.db.get_hidden_packages()
        for row in rows:
            self.cio.writeln(self.format_package(row), level)

cli().run()
