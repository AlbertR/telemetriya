# -*- coding: utf-8 -*-

from __future__ import with_statement

from cgi import escape
from functools import wraps
from flask import current_app, redirect, request, flash, g, json, render_template, Markup, \
    _request_ctx_stack, session
from flask.ext.wtf import Form, file_allowed, file_required
from flask.ext.uploads import UploadSet, IMAGES
from flask.ext.security import  current_user, login_user #, login_required
from wtforms import validators, Field, TextField, FileField, BooleanField, \
    SelectField, HiddenField
#from wtforms.validators import Required, DataRequired
from werkzeug import secure_filename
from werkzeug.local import LocalProxy
from telemetriya import app, db
import resources
import json
from datetime import datetime, timedelta
import re
import barcode
from barcode.writer import ImageWriter
from .decorators import login_required, role_required

log = app.logger
images = UploadSet("images", IMAGES)
reg_active = False

#login_manager = LoginManager()
#print login_manager
#print resources.model.security
#print "test"
#print app

### Decorators

# current_user = LocalProxy(lambda: _request_ctx_stack.top.user)

def html_params(**kwargs):
    """
    Generate HTML parameters from inputted keyword arguments.

    The output value is sorted by the passed keys, to provide consistent output
    each time this function is called with the same parameters.  Because of the
    frequent use of the normally reserved keywords `class` and `for`, suffixing
    these with an underscore will allow them to be used.

    >>> html_params(name='text1', id='f', class_='text')
    u'class="text" id="f" name="text1"'
    """
    params = []
    for k,v in sorted(kwargs.iteritems()):
        if k in ('class_', 'class__', 'for_'):
            k = k[:-1]
        if v is True:
            params.append(k)
        else:
            params.append(u'%s="%s"' % (unicode(k), escape(unicode(v), quote=True)))
    return u' '.join(params)

def register_active(f):
    @wraps(f)
    def active(*args, **kwargs):
        if reg_active:
            print 'register acitive'
            res = f(*args, **kwargs)
            return res
        print 'register disactive'
    return active

def fill_selects():

    k = 0
    g.temperature = []
    # Temperature range from -60 to 60 degrees Celsius
    for t in range(-60, 61):
        g.temperature.append((k,t))
        k+=1
    # Humidity in the range from 0 to 100%
    k = 0
    g.relative_humidity = []
    for t in range (0, 101):
        g.relative_humidity.append((k,t))
        k+=1
    # Cloud options
    g.cloud = [(0, u'ясно'),(1, u'преимущественн_солнце'),(2, u'переменная'),(3, u'преимущественно_облачно'),(4, u'облачно'),(5, u'туман')]
    # Precipitation options
    g.precipitation = [(0, u'есть'),(1, u'нет')]
    # Coating temperature
    k = 0
    g.tcoating = []
    for t in range (-60, 101):
        g.tcoating.append((k,t))
        k+=1
    # Condition coverage
    g.coverage = [(0, u'сухо'), (1, u'немного влажное'),(2, u'влажное'),(3, u'сильно влажное'),(4, u'лужи')]
    # Label status
    g.lstatus = [(0, u'ок'),(1, u'отключена'),(2,u'розыск')]
    # User status
    g.ustatus = [(0, u'BAN'),(1, u'ок'),(2, u'невидимка'),(3, u'розыск')]
    return

def get_weather():
    '''
    Get installed weather
    '''
    rm=resources.model

    weather = db.session.query(rm.Training).filter_by(active='1').first()

    return weather

def generate_tag(value):
   '''
   Generate a nine-line string
   '''
   str_label_id=str(value)
   if len(str_label_id)<9:
       i=len(str_label_id)
       while i < 9:
           str_label_id='0'+str_label_id
           i+=1
   value = re.sub(r'(\d)(?=(\d\d\d)+([^\d]|$))|$',r'\g<0>.', str_label_id)[:-1]
   return value

def find_user(**kwargs):

    rm = resources.model

    return db.session.query(rm.User).filter_by(**kwargs).first()

def create_user_method():
    '''
    Create User
    '''

    return

def minValue(value):
    '''
    Поиск минимального числа в массиве и получение его порядкового номера
    '''
    array_index = 0
    j = 0
    min = value[0]
    for i in value:
        if i < min:
            min = i
            array_index = j
        j += 1
    return array_index

def circleDelta(value):
    '''
    Разница времени прохождения текущего круга и предыдущего
    '''
    delta = []
    delta.append('0')
    for i in range(0,7):
        try:
            deltaValue = value[i+1]-value[i]
            if deltaValue > 0:
                delta.append("+"+str(deltaValue))
            else:
                delta.append(str(deltaValue))
        except:
            pass
    return delta

def bestlap(value):
    pass

class InlineButtonWidget(object):
    html_params = staticmethod(html_params)

    def __init__(self, input_type='submit', text=''):
        self.input_type = input_type
        self.text = text

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('type', self.input_type)
        if 'value' not in kwargs:
            kwargs['value'] = field._value()
        return Markup('<button type="submit" %s><span>%s</span></button>' % (self.html_params(name=field.name, **kwargs), field.text))

class InlineButton(Field):
  widget = InlineButtonWidget()

  def __init__(self, label=None, validators=None, text='Save', **kwargs):
    super(InlineButton, self).__init__(label, validators, **kwargs)
    self.text = text

  def _value(self):
        if self.data:
            return u''.join(self.data)
        else:
            return u''

class AdminBaseForm(Form):

    b_drop = BooleanField("Drop tables")
    btn_create = InlineButton('', text='Create bases', description='Create bases')
    btn_begin_track = InlineButton('', text=u'Начать тренировку', description='Begin training')
    btn_track_controll = InlineButton('', text=u'Управление треками', description='Track controll')
    btn_label_controll = InlineButton('', text=u'Управление метками', description='Label controll')
    btn_user_controll = InlineButton('', text=u'Управление пользователями', description='User controll')
    btn_admin_controll = InlineButton('', text=u'Администрирование', description='Admin controll')
    btn_statistics = InlineButton('', text=u'Статистика', description='Statistics')

class RegisterForm(Form):

    lastname = TextField("lastname", [validators.InputRequired(message=(u'Необходимо ввести фамилию')),validators.NoneOf(values=(u'Фамилия'))])
    firstname = TextField("firstname", [validators.InputRequired(message=(u'Необходимо ввести имя'))]) #

    patronymic = TextField("patronymic")
    nickname = TextField("nickname")
    phone = TextField("phone", [validators.required(message=(u'Необходимо ввести телефон'))]) #
    email = TextField("email", [validators.required(message=(u'Необходимо ввести e-mail'))]) #
    agree = BooleanField("agreement")
    btn_ok = InlineButton('', text=u'Зарегистрировать', description=u'Зарегистрировать')
    btn_cancel = InlineButton('', text=u'Отменить', description=u'Отменить')

class LoginForm(Form):

    login = TextField("login")
    password = HiddenField("password")
    btn_ok = InlineButton('', text=u'', description=u'login')

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)

    def validate(self):

        if self.login.data.strip() == '':
            return False

        self.user = find_user(user_phone=self.login.data)

        if self.user is None:
            g.user_unexists = 1
            return False

        return True

class CreateTraining(Form):

    temperature = SelectField(u"test", coerce=int)
    relative_humidity = SelectField(u'humidity', coerce=int)
    cloudiness = SelectField(u'cloudiness', coerce=int)
    precipitation = SelectField(u'precipitation', coerce=int)
    tcoating = SelectField(u'coating', coerce=int)
    ccoverage = SelectField(u'coverage', coerce=int)
    track = SelectField(u'track', coerce=int)
    stop = TextField("stop")
    btn_ok = InlineButton('', text=u'Начать тренировку', description=u'Начать тренировку')
    btn_cancel = InlineButton('', text=u'Отменить', description=u'Отменить')

class ControllLabel(Form):

    create_label = InlineButton('', text=u'СОЗДАТЬ НОВУЮ МЕТКУ', description=u'Создать новую метку')
    back_to_menu = InlineButton('', text=u'НАЗАД В МЕНЮ', description=u'Назад')

class CreateLabel(Form):

    label_id = TextField('label_id')
    status = SelectField('status', coerce=int)
    btn_ok = InlineButton('', text=u'СОЗДАТЬ', description=u'Создать')
    btn_cancel = InlineButton('', text=u'ОТМЕНИТЬ', description=u'Отменить')

class EditLabel(Form):

    label_id = TextField('label_id')
    labelid = HiddenField('id')
    status = SelectField('status', coerce=int)
    btn_ok = InlineButton('', text=u'ПРИМЕНИТЬ', description=u'Применить')
    btn_del = InlineButton('', text=u'', description=u'Удалить')
    btn_cancel = InlineButton('', text=u'ОТМЕНИТЬ', description=u'Отменить')

class UserLogin(Form):

    user_phone = TextField('label_id')
    btn_ok = InlineButton('', text=u'', description=u'OK')
    btn_register = InlineButton('', text=u'РЕГИСТРАЦИЯ НОВОГО ПОЛЬЗОВАТЕЛЯ', description=u'Регистрация')
    btn_return = InlineButton ('', text=u'ВОЗВРАТ МЕТКИ', description=u'Возврат метки')

    def validate(self):

        if self.user_phone.data.strip() == '':
            return False

        self.user = find_user(user_phone=self.user_phone.data)

        if self.user is None:
            g.user_unexists = 1
            return False

        return True

class GetLabel(Form):

    label_id = TextField('label_id')
    btn_ok = InlineButton('', text=u'', description=u'')
    btn_cancel = InlineButton ('', text=u'ОТМЕНИТЬ', description=u'ОТМЕНИТЬ')

class ReturnLabel(Form):

    user_phone = TextField('label_id')
    btn_user_ok = InlineButton('', text=u'', description=u'OK')
    label_id = TextField('label_id')
    btn_ok = InlineButton('', text=u'ПРИНЯТЬ МЕТКУ', description=u'Принять метрку')
    btn_cancel = InlineButton ('', text=u'В НАЧАЛО', description=u'В начало')

    def validate(self):

        if current_user.is_anonymous():
            if self.user_phone.data.strip() == '':
                return False

            self.user = find_user(user_phone=self.user_phone.data)

            if self.user is None:
                g.user_unexists = 1
                return False

        if current_user.is_active():
            if self.label_id.data.strip() == '':
                return False

        return True

class TrackControll(Form):

    create_track = InlineButton('', text=u'СОЗДАТЬ НОВЫЙ ТРЕК', description=u'Создать новый трек')
    back_to_menu = InlineButton('', text=u'НАЗАД В МЕНЮ', description=u'Назад')

class CreateTrack(Form):

    trackname = TextField("trackname") #, [validators.InputRequired(message=(u'Необходимо ввести название трека')), validators.NoneOf(values=(u'Название'))])
    trackid = HiddenField("id")
    length = TextField("length")
    country = TextField("country")
    gps = TextField("gps")
    mintime = TextField("mintime") #, [validators.InputRequired(message=(u'Необходимо ввести минимальное время трека')), validators.NoneOf(values=(u'Минимальное время'))])
    maxtime = TextField("maxtime") #, [validators.InputRequired(message=(u'Необходимо ввести максимальное время трека')), validators.NoneOf(values=(u'Максимальное время'))])
    active = BooleanField()
    btn_ok = InlineButton('', text=u'СОЗДАТЬ', description=u'Создать')
    btn_update = InlineButton('', text=u'ПРИМЕНИТЬ', description=u'Применить')
    back_to_menu = InlineButton('', text=u'НАЗАД В МЕНЮ', description=u'Отменить')

class ControllUser(Form):

    create_user = InlineButton('', text=u'СОЗДАТЬ НОВОГО ПОЛЬЗОВАТЕЛЯ', description=u'Создать')
    back_to_menu = InlineButton('', text=u'НАЗАД В МЕНЮ', description=u'Назад')

class EditUser(Form):

    userid = TextField("userid")
    usertag = TextField("usertag")
    lastname = TextField("lastname") #, [validators.InputRequired(message=(u'Необходимо ввести фамилию')),validators.NoneOf(values=(u'Фамилия'))])
    firstname = TextField("firstname") #, [validators.InputRequired(message=(u'Необходимо ввести имя'))])
    patronymic = TextField("patronymic")
    nickname = TextField("nickname")
    phone = TextField("phone") #, [validators.required(message=(u'Необходимо ввести телефон'))])
    email = TextField("email") #, [validators.required(message=(u'Необходимо ввести e-mail'))])
    status = SelectField("status", coerce=int)
    note = TextField("note")
    btn_ok = InlineButton('', text=u'ПРИМЕНИТЬ', description=u'Применить')
    btn_cancel = InlineButton('', text=u'ОТМЕНИТЬ', description=u'Отменить')

class CreatedUser(Form):

    userinfo = TextField("userinfo")
    user_tag = TextField("user_tag")
    btn_ok = InlineButton('', text=u'В НАЧАЛО', description=u'В начало')

class StatisticsForm(Form):

    temperature = SelectField(u"test", coerce=int)
    relative_humidity = SelectField(u'humidity', coerce=int)
    cloudiness = SelectField(u'cloudiness', coerce=int)
    #precipitation = SelectField(u'precipitation', coerce=int)
    tcoating = SelectField(u'coating', coerce=int)
    ccoverage = SelectField(u'coverage', coerce=int)
    btn_start_session = InlineButton('', text=u'НАЧАТЬ СЕССИЮ', description=u'Начать сессию')
    btn_stop = InlineButton('', text=u'ЗАВЕРШИТЬ ТРЕНИРОВКУ', description=u'Завершить тренировку')

@app.route('/login', methods=['GET','POST'])
def login():

    #form = LoginForm()
    rm = resources.model
    form = UserLogin()
    # g.last_login = ''
    if form.validate_on_submit():

        login_user(form.user, remember=False)
        flash("Logged is successfully.")
        if session['referer'] != '':
            if session["referer"] == '/':
                label_user = db.session.query(rm.Label).filter_by(user_id=current_user.id).first()
                if label_user:
                    return redirect('/')
                else:
                    return redirect('/get_label')
            else:
                return redirect(session['referer'])
        else:
            return redirect('/get_label')
    else:
        if request.form.getlist('btn_register'):
            return redirect('/register')
        if request.form.getlist('btn_return'):
            return redirect('/return_label')

    return render_template('register_label.html', form=form)

@app.route('/', methods=['GET', 'POST'])
@login_required
def root():

    '''
    проверить есть ли у пользователя метка, если метки нет,
    то вывести окно привязки метки к пользователю, если метка
    есть, то вывести статистику по этой метке.
    '''
    rm = resources.model
    fill_selects()
    label_id = db.session.query(rm.Label).filter_by(user_id=current_user.id).all()
    minimumValue = []
    circDelta = []
    if label_id:
        # получить активную тренировку
        training = db.session.query(rm.Training).filter_by(active=1).first()
        if not training:

            class Training(object):

                def __init__(self, session):
                    self.session = session
                    return

                def json_dump(self):
                    return dict(sesson=self.session)

            training = Training(u"STP")
            training_date = datetime.now()
        else:
            training_date = training.date
        print training_date
        # получить зарегистрированные метки
        labels = db.session.query(rm.Label).filter(rm.Label.user_id > 0).all()
        all_data = []
        userinfo = []
        best_lap = []
        for l in labels:
            ringtimeValue = [] # список времен кругов
            data_statistics=[] # список данных за неколько (10) кругов
            stat = db.session.query(rm.Statistics).\
                   filter(rm.Statistics.user_id==l.user_id, rm.Statistics.date>=training_date).\
                   order_by(rm.Statistics.id.desc()).limit(8).all() # , rm.Statistics.date>training.date
            user = db.session.query(rm.User).filter_by(id=l.user_id).first()
            user_info = db.session.query(rm.UserInfo).filter_by(id=user.user_info).first()
            userinfo.append(user_info.user_lname+" ["+user_info.user_nickname+"] "+user_info.user_fname)
            for line in stat:
                ringtimeValue.insert(0,line.ringtime) # добавить время круга в список
                converted_data = line.json_dump()
                m,s = divmod(int(line.ringtime), 60)
                drob = int((line.ringtime - int(line.ringtime))*10000)
                time_from_track = "%02d:%02d.%d" % (m,s,drob)
                line.ringtime = str(time_from_track)
                data_statistics.insert(0, line.json_dump())
            if stat != []:
                all_data.append(data_statistics)
                minimumValue.insert(0,minValue(ringtimeValue))
                best = db.session.query(rm.Statistics).\
                       filter(rm.Statistics.user_id==l.user_id, rm.Statistics.date>=training.date).\
                       order_by(rm.Statistics.ringtime.asc()).first()
                best_lap.append(best.ringtime)
                circDelta.append(circleDelta(ringtimeValue))
                print best_lap
    else:
        return redirect('/get_label')

    return render_template("users_statistics.html", training=training, alldata=all_data, minimumValue=minimumValue, circDelta=circDelta, userinfo=userinfo, best_lap=best_lap)

@app.route('/admin', methods=['GET', 'POST'])
@role_required
@login_required
def admin():
    '''
    Admin function
    '''

    status_arr = ('active', 'deny', 'off')
    rm = resources.model
    form = AdminBaseForm()
    fill_selects()
    weather = get_weather()
    if weather:
        track = db.session.query(rm.Track).filter_by(id=weather.track).first()
        g.session = weather.session
    else:
        track = False
    if not track:
        name = u"Трек не выбран"
    else:
        name = track.name
    if form.validate_on_submit():
        if form.b_drop.data and request.form.getlist('btn_create'):
            db.drop_all()
            print "db.drop_all"
            db.create_all()
            for s in status_arr:
                status = rm.Status(s)
                db.session.add(status)
            db.session.add(status)
            db.session.commit()
        elif form.b_drop.data!=1 and request.form.getlist('btn_create'):
            print "db.create_all"
            db.create_all()
        if request.form.getlist('btn_begin_track'):
            print "form.btn_begin_track"
            return redirect("/create_training")
        if request.form.getlist('btn_track_controll'):
            print "form.btn_track_controll"
            return redirect("/track_controll")
        if request.form.getlist('btn_label_controll'):
            print "form.btn_label_controll"
            return redirect("/controll_label")
        if request.form.getlist('btn_user_controll'):
            print "form.btn_user_controll"
            return redirect("/controll_user")
        if request.form.getlist('btn_admin_controll'):
            print "form.btn_admin_controll"
            return redirect("/controll_admin")
        if request.form.getlist('btn_statistics'):
            print "form.btn_statistics"
            return redirect("/statistics")
    return render_template('admin.html', form=form, track=name, weather=weather)

@app.route('/register', methods=['GET', 'POST'])
#@register_active()
def register():
    '''
    Register User (Tests for the match code create_user)
    '''
    rm = resources.model
    form = RegisterForm()
    fill_selects()
    weather = get_weather()
    if weather:
        track = db.session.query(rm.Track).filter_by(id=weather.track).first()
    else:
        track = False
    if not track:
        name = u"Трек не выбран"
    else:
        name = track.name
        g.session = weather.session

    if form.validate_on_submit():
        if request.form.getlist('agree'):
            if request.form.getlist('btn_ok'):
                rf = request.form
                user = rm.user_datastore.create_user(user_tag='', email=rf.getlist('email')[0], user_phone=rf.getlist('phone')[0])
                userinfo = rm.UserInfo(user=user, user_lname=rf.getlist('lastname')[0].encode('utf-8'), user_fname=rf.getlist('firstname')[0].encode("utf-8"), user_patronymic=rf.getlist('patronymic')[0].encode("utf-8"), user_nickname=rf.getlist('nickname')[0].encode("utf-8"), user_status=1, user_why=' '.encode("utf-8"))
                db.session.add(userinfo)
                db.session.commit()
                usertag = "u"+generate_tag(user.id)
                db.session.query(rm.User).filter_by(id=user.id).update({'user_tag':usertag})
                db.session.commit()
                '''
                Generate barcode
                '''
                # print usertag.encode('utf-8')
                ean = barcode.get_barcode('code39', usertag, writer=ImageWriter())
                filename = ean.save('telemetriya/static/img/code39')
                return redirect('/created_user/%s' % userinfo.id)
            elif request.form.getlist('btn_cancel'):
                return redirect('/admin')
    else:
        if request.form.getlist('btn_cancel'):
            return redirect('/admin')
        elif request.form.getlist('btn_ok'):
            g.validator_not_passed = 1

    return render_template('register.html', form=form, track=name, weather=weather)

@app.route('/create_training', methods=['GET', 'POST'])
@role_required
@login_required
def create_training():
    '''
    Create training parameters
    '''
    print 'create_training'
    rm = resources.model
    form = CreateTraining()

    fill_selects()

    form.temperature.choices = g.temperature
    form.relative_humidity.choices = g.relative_humidity
    form.cloudiness.choices = g.cloud
    form.precipitation.choices = g.precipitation
    form.tcoating.choices = g.tcoating
    form.ccoverage.choices = g.coverage
    query = db.session.query(rm.Track).filter_by(active='1')
    choices = []
    for q in query:
        choices.append((q.id, q.name))
    form.track.choices = choices
    weather = db.session.query(rm.Training).filter_by(active='1').first()
    if weather:
        name_query = db.session.query(rm.Track).filter_by(id=weather.track).first()
        if name_query.active==True:
            name = name_query.name
            g.session = weather.session
        else:
            name = u'Трек не активен'
        print weather.json_dump()
    else:
        name = u'Тренировка не создана'
    # if weather:
    #     print weather.json_dump()
    if form.validate_on_submit():
        rf = request.form
        db.session.query(rm.Training).filter_by(active='1').update({'active':'0','stop':datetime.now()})
        training = rm.Training(temperature=rf.getlist('temperature')[0], relative_humidity=rf.getlist('relative_humidity')[0], cloudiness=rf.getlist('cloudiness')[0], precipitation=rf.getlist('precipitation')[0], tcoating=rf.getlist('tcoating')[0], ccoverage=rf.getlist('ccoverage')[0], start=datetime.now(), stop=u"00:00:00", duration=u"0", track=rf.getlist('track')[0], session='1', active='1')
        print training
        db.session.add(training)
        db.session.commit()
        return redirect('/admin')
    return render_template('create_training.html', form=form, track=name, weather=weather, list = weather)

@app.route('/controll_label', methods=['GET', 'POST'])
@role_required
@login_required
def controll_label():
    '''
    Label controll
    '''
    rm = resources.model
    form = ControllLabel()
    fill_selects()
    weather = get_weather() # db.session.query(rm.Training).filter_by(active='1').first()
    if weather:
        track = db.session.query(rm.Track).filter_by(id=weather.track).first()
    else:
        track = False
    label = db.session.query(rm.Label).order_by(rm.Label.label_id)
    for item in label:
        str_label_id=str(item.label_id)
        if len(str_label_id)<9:
            i=len(str_label_id)
            while i < 9:
                str_label_id='0'+str_label_id
                i+=1
        item.label_id=re.sub(r'(\d)(?=(\d\d\d)+([^\d]|$))|$', r'\g<0>.', str_label_id)[:-1]
    if not track:
        name = u"Трек не выбран"
    else:
        name = track.name
    if form.validate_on_submit():
        if request.form.getlist('create_label'):
            return redirect('/create_label')
        if request.form.getlist('back_to_menu'):
            return redirect('/admin')
    return render_template('controll_label.html', form=form, track=name, weather=weather, list=label)

@app.route('/create_label', methods=['GET', 'POST'])
@role_required
@login_required
def create_label():
    '''
    Create label
    '''
    rm=resources.model
    form = CreateLabel()
    fill_selects()
    # weather = db.session.query(rm.Training).filter_by(active='1').first()
    weather = get_weather()
    if weather:
        track = db.session.query(rm.Track).filter_by(id=weather.track).first()
    else:
        track = False
    form.status.choices = g.lstatus
    if not track:
        name = u"Трек не выбран"
    else:
        name = track.name
    print request.form
    if form.validate_on_submit():
        if request.form.getlist('btn_ok'):
            rf=request.form
            label_id=re.sub(r'(\.)+',r'',rf.getlist('label_id')[0])
            label = rm.Label(label_id=label_id, status=rf.getlist('status')[0], user_id='')
            db.session.add(label)
            db.session.commit()
            return redirect('/controll_label')
        if request.form.getlist('btn_cancel'):
            return redirect('/admin')
    return render_template('create_label.html', form=form, track=name, weather=weather)

@app.route('/edit_label/<label_id>', methods=['GET', 'POST'])
@role_required
@login_required
def edit_label(label_id):
    '''
    Label edit
    '''

    print 'edit_label'
    rm=resources.model
    form=EditLabel()
    fill_selects()
    weather = get_weather()
    if weather:
        track = db.session.query(rm.Track).filter_by(id=weather.track).first()
        g.session = weather.session
    else:
        track = False
    form.status.choices = g.lstatus
    if not track:
        name = u"Трек не выбран"
    else:
        name = track.name
    print request.form
    if form.validate_on_submit():
        rf = request.form
        if rf.getlist('btn_ok'):
            print rf.getlist('labelid')[0]
            db.session.query(rm.Label).filter_by(id=rf.getlist('labelid')[0]).update({'status': rf.getlist('status')[0]})
            db.session.commit()
            return redirect('/controll_label')
        if rf.getlist('btn_del'):
            db.session.query(rm.Label).filter_by(id=rf.getlist('labelid')[0]).delete()
            db.session.commit()
            return redirect('/controll_label')
        if rf.getlist('btn_cancel'):
            return redirect('/controll_label')
    else:
        query = db.session.query(rm.Label).filter_by(id=label_id).first()
        str_label_id=str(query.label_id)
        if len(str_label_id)<9:
            i=len(str_label_id)
            while i < 9:
                str_label_id='0'+str_label_id
                i+=1
        query.label_id = re.sub(r'(\d)(?=(\d\d\d)+([^\d]|$))|$',r'\g<0>.', str_label_id)[:-1]
        print query.json_dump()
    return render_template('edit_label.html', form=form, weather=weather,track=name, list=query)

@app.route('/register_label', methods=['GET', 'POST'])
@role_required
@login_required
def register_label():
    return

@app.route('/get_label', methods=['GET','POST'])
@login_required
def get_label():
    '''
    Get Label
    '''
    rm = resources.model
    form = GetLabel()
    fill_selects()
    weather = get_weather()
    if weather:
        track = db.session.query(rm.Track).filter_by(id=weather.track).first()
        g.session = weather.session
    else:
        track = False
    if not track:
        name = u"Трек не выбран"
    else:
        name = track.name
    # print current_user.id
    user_info = db.session.query(rm.UserInfo).filter_by(id=current_user.user_info).first()
    if form.validate_on_submit():
        rf = request.form
        if rf.getlist('btn_ok'):
            label_id=re.sub(r'(\.)+',r'',rf.getlist('label_id')[0])
            # print label_id
            '''
        у пользователя еще не сдана предыдущая метка
        '''
        user_has_label = db.session.query(rm.Label).filter_by(user_id=current_user.id).first()
        if user_has_label:
            print "user_has_label"
            g.user_has_label = 1
            return render_template('/get_label.html', form=form, weather=weather, \
                       track=name, user_info=user_info)
        '''
        проверить не привязана ли уже эта метка к пользователю
        '''
        label_mounted = db.session.query(rm.Label).filter_by(label_id=label_id).first()
        if label_mounted.user_id:
            print label_mounted
            g.label_mounted = 1
        else:
            db.session.query(rm.Label).filter_by(label_id=label_id).update({'user_id':current_user.id})
            db.session.commit()
            return redirect('/')
        if rf.getlist('btn_cancel'):
            return redirect('/get_label')
    return render_template('/get_label.html', form=form, weather=weather, \
                           track=name, user_info=user_info)

@app.route('/return_label', methods=['GET', 'POST'])
#@role_required
#@login_required
def return_label():
    '''
    Retrun label
    '''

    rm = resources.model
    fill_selects()
    weather = get_weather()
    if weather:
        track = db.session.query(rm.Track).filter_by(id=weather.track).first()
        g.session = weather.session
    else:
        track = False
    if not track:
        name = u"Трек не выбран"
    else:
        name = track.name
    form = ReturnLabel()
    if current_user.is_anonymous():
        g.anonymous = 1
        user_info = None
    else:
        g.anonymous = 0
        user_info = db.session.query(rm.UserInfo).filter_by(id=current_user.user_info).first()
    if form.validate_on_submit():
        rf = request.form
        if rf.getlist('btn_user_ok'):
            login_user(form.user, remember=False)
            if current_user.is_active():
                g.anonymous = 0
                user_info = db.session.query(rm.UserInfo).filter_by(id=current_user.user_info).first()
        if rf.getlist('btn_ok'):
            label=re.sub(r'(\.)+',r'',rf.getlist('label_id')[0])
            label_id = db.session.query(rm.Label).filter_by(label_id=label).first()
            if label_id == None:
                g.label_id = 'None'
                return render_template('return_label.html', form=form, weather=weather, track=name, user_info=user_info)
            if label_id != None and label_id.user_id == 0:
                g.label_id = 0
                return render_template('return_label.html', form=form, weather=weather, track=name, user_info=user_info)
            if label_id != None and label_id.user_id > 0:
                # g.label_id = label_id.label_id
                db.session.query(rm.Label).filter_by(label_id=label).update({'user_id':0})
                db.session.commit()
                return render_template('return_label.html', form=form, weather=weather, track=name, user_info=user_info)
        if rf.getlist('btn_cancel'):
            return redirect('/admin')
    return render_template('return_label.html', form=form, weather=weather, track=name, user_info=user_info)

@app.route('/track_controll', methods=['GET', 'POST'])
@role_required
@login_required
def track_controll():
    '''
    Track controll
    '''
    fill_selects()

    form = TrackControll()
    rm=resources.model
    fill_selects()
    weather = get_weather()
    if weather:
        track = db.session.query(rm.Track).filter_by(id=weather.track).first()
        g.session = weather.session
    else:
        track = False
    if not track:
        name = u"Трек не выбран"
    else:
        name = track.name
    query = db.session.query(rm.Track).all()
    weather = db.session.query(rm.Training).filter_by(active='1').first()
    # print weather.json_dump()
    if form.validate_on_submit():
        if request.form.getlist('create_track'):
            return redirect('/create_track')
        if request.form.getlist('back_to_menu'):
            return redirect('/admin')
    return render_template('track_controll.html', form=form, track=name, weather=weather, list=query)

@app.route('/create_track', methods=['GET', 'POST'])
@role_required
@login_required
def create_track():
    '''
    Create track
    '''
    rm=resources.model
    form = CreateTrack()
    fill_selects()
    weather = get_weather()
    if weather:
        track = db.session.query(rm.Track).filter_by(id=weather.track).first()
        g.session = weather.session
    else:
        track = False
    if not track:
        name = u"Трек не выбран"
    else:
        name = track.name
    if form.validate_on_submit():
        if request.form.getlist('btn_ok'):
            rf = request.form
            print rf
            name = 'Без названия' if rf.getlist('trackname')[0].encode('utf-8')=='Название' else rf.getlist('trackname')[0].encode('utf-8')
            length = '' if rf.getlist('length')[0].encode('utf-8')=='Протяженность' else rf.getlist('length')[0].encode('utf-8')
            address = '' if rf.getlist('country')[0].encode('utf-8')=='Адрес' else rf.getlist('country')[0].encode('utf-8')
            gps = '' if rf.getlist('gps')[0].encode('utf-8')=='Координаты (через запятую)' else rf.getlist('gps')[0].encode('utf-8')
            mintime = '00:00' if rf.getlist('mintime')[0].encode('utf-8')=='00:00' else rf.getlist('mintime')[0].encode('utf-8')
            maxtime = '00:00' if rf.getlist('maxtime')[0].encode('utf-8')=='00:00' else rf.getlist('maxtime')[0].encode('utf-8')
            active = '1' if rf.getlist('active') else '0'

            track = rm.Track(name=name, length=length, address=address, gps=gps, mintime=mintime, maxtime=maxtime, active=active)
            # if active=='1':
            #     db.session.query(rm.Track).filter_by(active='1').update({'active':'0'})
            db.session.add(track)
            db.session.commit()
            return redirect('/admin')
        if request.form.getlist('back_to_menu'):
            return redirect('/admin')
    return render_template('create_track.html', form=form, track=name, weather=weather)

@app.route('/track_edit/<track_id>', methods=['GET', 'POST'])
@role_required
@login_required
def edit_track(track_id):
    '''
    Track edit
    '''
    print request.form
    rm=resources.model
    form = CreateTrack()
    fill_selects()
    weather = get_weather()
    if weather:
        track = db.session.query(rm.Track).filter_by(id=weather.track).first()
        g.session = weather.session
    else:
        track = False
    if not track:
        name = u"Трек не выбран"
    else:
        name = track.name
    if form.validate_on_submit():
        rf=request.form
        name = 'Без названия' if rf.getlist('trackname')[0].encode('utf-8')=='Название' else rf.getlist('trackname')[0].encode('utf-8')
        length = '' if rf.getlist('length')[0].encode('utf-8')=='Протяженность' else rf.getlist('length')[0].encode('utf-8')
        address = '' if rf.getlist('country')[0].encode('utf-8')=='Адрес' else rf.getlist('country')[0].encode('utf-8')
        gps = '' if rf.getlist('gps')[0].encode('utf-8')=='Координаты (через запятую)' else rf.getlist('gps')[0].encode('utf-8')
        mintime = '00:00' if rf.getlist('mintime')[0].encode('utf-8')=='00:00' else rf.getlist('mintime')[0].encode('utf-8')
        maxtime = '00:00' if rf.getlist('maxtime')[0].encode('utf-8')=='00:00' else rf.getlist('maxtime')[0].encode('utf-8')
        active = '1' if rf.getlist('active') else '0'
        if not rf.getlist('back_to_menu'):
                # db.session.query(rm.Track).filter_by(active='1').update({'active':'0'})
                db.session.query(rm.Track).filter_by(id=rf.getlist('trackid')[0]).update({'name':name,'length':length,'address':address,'gps':gps,'mintime':mintime,'maxtime':maxtime,'active':active})
                db.session.commit()
        return redirect('/track_controll')
    else:
        query = db.session.query(rm.Track).filter_by(id=track_id).first()
        #print json.dumps(query.json_dump())
        query.name = u"Название" if query.name=="" else query.name
        query.length = u"Протяженность" if query.length==0 else query.length
        query.address = u"Адрес" if query.address=="" else query.address
        query.gps = u"Координаты (через запятую)" if query.gps=="" else query.gps
        query.mintime = u"00:00" if query.mintime=="00:00:00" else query.mintime
        query.maxtime = u"00:00" if query.maxtime=="00:00:00" else query.maxtime
        if query.active==1:
            form.active.data="True"
    return render_template('edit_track.html', form=form, title=u'Редактирование трека', track=name, weather = weather, list=query)

@app.route('/controll_user', methods=['GET', 'POST'])
@role_required
@login_required
def controll_user():
    '''
    Controll Users
    '''

    rm = resources.model
    form = ControllUser()
    fill_selects()
    weather = db.session.query(rm.Training).filter_by(active='1').first()
    if weather:
        track = db.session.query(rm.Track).filter_by(id=weather.track).first()
        g.session = weather.session
    else:
        track = False
    user = db.session.query(rm.UserInfo).order_by(rm.UserInfo.id)
    if not track:
        name = u"Трек не выбран"
    else:
        name = track.name
    if form.validate_on_submit():
        if request.form.getlist('create_user'):
            return redirect('/create_user')
        if request.form.getlist('back_to_menu'):
            return redirect('/admin')
    return render_template('controll_user.html', form=form, track=name, weather=weather, list=user)

@app.route('/create_user', methods=['GET', 'POST'])
@role_required
@login_required
def create_user():
    '''
    Create User (Tests for the match code register)
    '''
    rm = resources.model
    form = RegisterForm()
    fill_selects()
    weather = get_weather()
    if weather:
        track = db.session.query(rm.Track).filter_by(id=weather.track).first()
    else:
        track = False
    if not track:
        name = u"Трек не выбран"
    else:
        name = track.name
        g.session = weather.session
    print request.form
    if form.validate_on_submit():
        # if request.form.getlist('agree'):
        if request.form.getlist('btn_ok'):
            rf = request.form
            user = rm.user_datastore.create_user(user_tag='', email=rf.getlist('email')[0], user_phone=rf.getlist('phone')[0])
            userinfo = rm.UserInfo(user=user, user_lname=rf.getlist('lastname')[0].encode('utf-8'), user_fname=rf.getlist('firstname')[0].encode("utf-8"), user_patronymic=rf.getlist('patronymic')[0].encode("utf-8"), user_nickname=rf.getlist('nickname')[0].encode("utf-8"), user_status=1, user_why=' '.encode("utf-8"))
            db.session.add(userinfo)
            db.session.commit()
            usertag = "u"+generate_tag(user.id)
            db.session.query(rm.User).filter_by(id=user.id).update({'user_tag':usertag})
            db.session.commit()
            '''
            Generate barcode
            '''
            print usertag.encode('utf-8')
            ean = barcode.get_barcode('code39', usertag, writer=ImageWriter())
            filename = ean.save('telemetriya/static/img/code39')
            return redirect('/created_user/%s' % userinfo.id)
        elif request.form.getlist('btn_cancel'):
            return redirect('/get_label')
    else:
        if request.form.getlist('btn_cancel'):
            return redirect('/get_label')
        elif request.form.getlist('btn_ok'):
            g.validator_not_passed = 1

    return render_template('create_user.html', form=form, track=name, weather=weather)

@app.route('/edit_user/<user_id>', methods=['GET', 'POST'])
@role_required
@login_required
def edit_user(user_id):
    '''
    Edit User
    '''
    rm = resources.model
    form = EditUser()
    fill_selects()
    weather = get_weather()
    if weather:
        track = db.session.query(rm.Track).filter_by(id=weather.track).first()
    else:
        track = False
    if not track:
        name = u"Трек не выбран"
    else:
        name = track.name
        g.session = weather.session
    form.status.choices = g.ustatus
    if form.validate_on_submit():
        if request.form.getlist('btn_ok'):
            rf = request.form
            db.session.query(rm.UserInfo).filter_by(id=user_id).update({'user_lname': rf.getlist('lastname')[0], 'user_fname': rf.getlist('firstname')[0], 'user_patronymic': rf.getlist('patronymic')[0], 'user_nickname': rf.getlist('nickname')[0],'user_status':rf.getlist('status')[0], 'user_why':rf.getlist('note')[0]})
            db.session.query(rm.User).filter_by(user_info=user_id).update({'email':rf.getlist('email')[0], 'user_phone':rf.getlist('phone')[0]})
            db.session.commit()
            return redirect('/controll_user')
        elif request.form.getlist('btn_cancel'):
            return redirect('/admin')
    else:
        query = db.session.query(rm.UserInfo).filter_by(id=user_id).first()
        print query.json_dump()
        if request.form.getlist('btn_cancel'):
            return redirect('/admin')
        elif request.form.getlist('btn_ok'):
            g.validator_not_passed = 1

    return render_template('edit_user.html', form=form, track=name, weather=weather, list=query)

@app.route('/created_user/<user_id>', methods=['GET', 'POST'])
@role_required
@login_required
def created_user(user_id):
    '''
    Created User
    '''

    rm = resources.model
    form = CreatedUser()
    fill_selects()
    weather = get_weather()
    if weather:
        track = db.session.query(rm.Track).filter_by(id=weather.track).first()
    else:
        track = False
    if not track:
        name = u"Трек не выбран"
    else:
        name = track.name
        g.session = weather.session
    query = db.session.query(rm.UserInfo).filter_by(id=user_id).first()
    if form.validate_on_submit():
        if request.form.getlist('btn_ok'):
            return redirect("/admin")
    return render_template('created_user.html', form=form, track=name, weather=weather, list=query)

@app.route('/statistics', methods=['GET', 'POST'])
@role_required
@login_required
def statistics():
    '''
    Show training statistics
    '''

    rm = resources.model
    form = StatisticsForm()
    fill_selects()
    form.temperature.choices = g.temperature
    form.relative_humidity.choices = g.relative_humidity
    form.cloudiness.choices = g.cloud
    # form.precipitation.choices = g.precipitation
    form.tcoating.choices = g.tcoating
    form.ccoverage.choices = g.coverage
    weather = get_weather()
    if weather:
        track = db.session.query(rm.Track).filter_by(id=weather.track).first()
    else:
        track = False
    if not track:
        name = u"Трек не выбран"
    else:
        name = track.name
        g.session = weather.session
    if form.validate_on_submit():
        rf = request.form
        if rf.getlist("btn_start_session"):
            training = db.session.query(rm.Training).filter_by(active=1).first()
            session_num = training.session
            db.session.query(rm.Training).filter_by(id=training.id).update({'stop':datetime.now(),'active':0})
            db.session.commit()
            training = rm.Training(temperature=rf.getlist('temperature')[0], relative_humidity=rf.getlist('relative_humidity')[0], cloudiness=rf.getlist('cloudiness')[0], precipitation=training.precipitation, tcoating=rf.getlist('tcoating')[0], ccoverage=rf.getlist('ccoverage')[0], start=datetime.now(), stop=u"00:00:00", duration=u"0", track=training.track, session=training.session+1, active='1')
            db.session.add(training)
            db.session.commit()
        if rf.getlist("btn_stop"):
            db.session.query(rm.Training).filter_by(active=1).update({'active':0})
            db.session.commit()
    return render_template('admin_statistics.html', form=form, track=name, weather=weather)
