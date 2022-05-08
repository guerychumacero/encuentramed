from flask import Flask
from flask import render_template, request, redirect, url_for, flash, jsonify
from flaskext.mysql import MySQL
from flask import send_from_directory
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "chumacero"

mysql= MySQL()
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'sistema'
mysql.init_app(app)

CARPETA = os.path.join('uploads')
app.config['CARPETA'] = CARPETA

@app.route('/busquedas/index')
def busquedas():    
    page = request.args.get('page')
    if not page or int(page) == 0:
        page = 1    
    keyword = request.args.get('keyword')
    items = getItems(page, keyword)
    page_range = range(int(page) - 3, int(page) + 2)
    if int(page) < 4:
        page_range = range(1, int(page) + 4)
    return render_template('busquedas/index.html', items=items, page=int(page), prange = page_range)    

def getItems(page, keyword = None):
        sql = "SELECT i.nombre_comercial, n.nombre, f.nombre, c.nombre, p.nombre, pr.nombre, l.nombre, d.nombre, pu.precio, i.id, TRUNCATE((pu.peso_precio/10)/2,0) FROM insumo i INNER JOIN publicacion pu ON pu.id_insumo = i.id INNER JOIN forma_farmaceutica f ON f.id = i.id_forma_farmaceutica INNER JOIN concentracion c ON c.id = i.id_concentracion INNER JOIN presentacion p ON p.id = i.id_presentacion INNER JOIN proveedor pr ON pr.id = i.id_proveedor INNER JOIN nombre_generico n ON n.id = i.id_nombre_generico INNER JOIN lugar l ON l.id = pu.id_lugar INNER JOIN direccion d ON d.id = pu.id_direccion "
        conn = mysql.connect()
        cursor = conn.cursor() 
        if keyword:
            sql = sql + " where i.activo = 1 AND pu.activo = 1 AND pu.procesado = 1 AND pu.valido = 1 AND i.nombre_comercial like '%" + keyword + "%' ORDER BY pu.peso_precio DESC"
        start = (int(page) - 1) * 10
        sql = sql + " limit " + str(start) + ",13"
        cursor.execute(sql)
        items = cursor.fetchall()
        return items

@app.route("/obtenerFormaFarmaceutica",methods=["POST","GET"])
def obtenerFormaFarmaceutica():
    conn = mysql.connect()
    cursor = conn.cursor() 
    if request.method == 'POST':
        insumoId = request.form['insumoId']                
        cursor.execute("SELECT f.id as id_forma_farmaceutica, f.nombre as forma_farmaceutica FROM insumo i INNER JOIN forma_farmaceutica f ON f.id = i.id_forma_farmaceutica WHERE i.id_nombre_generico = (SELECT ins.id_nombre_generico FROM insumo ins WHERE ins.id = %s);", [insumoId])
        formasFarmaceuticas = cursor.fetchall()
        OutputArray = []
        for row in formasFarmaceuticas:
            outputObj = {
                'insumoId': row[0],
                'formaFarmaceutica': row[1]}
            OutputArray.append(outputObj)    
    return jsonify(OutputArray)    

@app.route('/uploads/<nombreFoto>')
def uploads(nombreFoto):    
    return send_from_directory(app.config['CARPETA'], nombreFoto)

@app.route('/')
def index():        
    page = request.args.get('page')
    if not page or int(page) == 0:        
        page = 1
    keyword = request.args.get('keyword')
    items = getItems(page, keyword)
    page_range = range(int(page) - 3, int(page) + 2)
    if int(page) < 4:
        page_range = range(1, int(page) + 4)
    return render_template('busquedas/index.html', items=items, page=int(page), prange = page_range)    

@app.route('/insumos')
def insumos():
    sql = "SELECT i.id as id_insumo, i.nombre_comercial, i.precio_unit_max_lab, i.precio_max_venta_distr, i.precio_unit_max_priv, gen.nombre AS nombre_generico, f.nombre AS forma_farmaceutica, c.nombre AS concentracion, p.nombre AS presentacion, pr.nombre AS proveedor FROM insumo i INNER JOIN nombre_generico gen ON gen.id = i.id_nombre_generico INNER JOIN forma_farmaceutica f ON f.id = i.id_forma_farmaceutica INNER JOIN concentracion c ON c.id = i.id_concentracion INNER JOIN presentacion p ON p.id = i.id_presentacion INNER JOIN proveedor pr ON pr.id = i.id_proveedor WHERE i.activo = 1 ORDER BY i.nombre_comercial ASC"
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sql)
    insumos = cursor.fetchall()    
    conn.commit()
    return render_template('insumos/index.html', insumos = insumos)

#ver luego lo de la foto
@app.route('/publicaciones')
def publicaciones():
    sql = "SELECT pu.id, i.nombre_comercial, n.nombre, f.nombre, c.nombre, p.nombre, pr.nombre, l.nombre, d.nombre, pu.precio FROM insumo i INNER JOIN publicacion pu ON pu.id_insumo = i.id INNER JOIN forma_farmaceutica f ON f.id = i.id_forma_farmaceutica INNER JOIN concentracion c ON c.id = i.id_concentracion INNER JOIN presentacion p ON p.id = i.id_presentacion INNER JOIN proveedor pr ON pr.id = i.id_proveedor INNER JOIN nombre_generico n ON n.id = i.id_nombre_generico INNER JOIN lugar l ON l.id = pu.id_lugar INNER JOIN direccion d ON d.id = pu.id_direccion where i.activo = 1 and pu.activo = 1"
    conn = mysql.connect()
    cursor = conn.cursor()    
    cursor.execute(sql)
    publicaciones = cursor.fetchall()    
    conn.commit()
    return render_template('publicaciones/index.html', publicaciones = publicaciones)

@app.route('/destroy/<int:id>')
def destroy(id):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT foto FROM empleados WHERE id = %s", (id))
    fila = cursor.fetchall()
    os.remove(os.path.join(app.config['CARPETA'], fila[0][0]))
    cursor.execute("DELETE FROM empleados WHERE id = %s", (id))
    conn.commit()
    return redirect('/')

@app.route('/edit/<int:id>')
def edit(id):    
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM empleados WHERE id = %s", (id))
    empleados = cursor.fetchall()
    conn.commit()
    return render_template('empleados/edit.html', empleados = empleados)

@app.route('/update', methods=['POST'])
def update():
    _nombre = request.form['txtNombre']
    _correo = request.form['txtCorreo']
    _foto = request.files['txtFoto']
    id = request.form['txtID']
    sql = "UPDATE empleados SET nombre = %s, correo = %s WHERE id = %s;"
    datos = (_nombre, _correo, id)
    conn = mysql.connect()
    cursor = conn.cursor()
    _now = datetime.now()
    tiempo = _now.strftime("%Y%H%M%S")
    if _foto.filename != '':
        nuevoNombreFoto = tiempo + _foto.filename
        _foto.save("uploads/" + nuevoNombreFoto)
        cursor.execute("SELECT foto FROM empleados WHERE id = %s", (id))
        fila = cursor.fetchall()
        os.remove(os.path.join(app.config['CARPETA'], fila[0][0]))
        cursor.execute("UPDATE empleados SET foto = %s WHERE id = %s", (nuevoNombreFoto, id))
        conn.commit()
    cursor.execute(sql, datos)
    conn.commit()
    return redirect('/')

@app.route('/create')
def create():
    #aqui poner una consulta para cargar el combo box de insumos
    sql = "SELECT s.id, s.nombre_comercial FROM insumo s WHERE s.activo = 1 order by s.nombre_comercial ASC"
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sql)
    insumos = cursor.fetchall()
    conn.commit()
    return render_template('empleados/create.html', insumos = insumos)

@app.route('/create_insumo')
def create_insumo():    
    sqlObtNombreGen = "SELECT g.id as id_nombre_generico, g.nombre as nombre_generico FROM nombre_generico g ORDER BY g.nombre ASC;"
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sqlObtNombreGen)
    nombresGenericos = cursor.fetchall()
    conn.commit()
    sqlObtFormaFarm = "SELECT f.id as id_forma_farmaceutica, f.nombre as forma_farmaceutica FROM forma_farmaceutica f ORDER BY f.nombre ASC;"
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sqlObtFormaFarm)
    formasFarmaceuticas = cursor.fetchall()
    conn.commit()
    sqlObtConcentracion = "SELECT c.id as id_concentracion, c.nombre as concentracion FROM concentracion c ORDER BY c.nombre ASC;"
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sqlObtConcentracion)
    concentraciones = cursor.fetchall()
    conn.commit()
    sqlObtPresentacion = "SELECT p.id as id_presentacion, p.nombre as presentacion FROM presentacion p ORDER BY p.nombre ASC;"
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sqlObtPresentacion)
    presentaciones = cursor.fetchall()
    conn.commit()
    sqlObtProveedores = "SELECT pr.id as id_proveedor, pr.nombre as proveedor FROM proveedor pr ORDER BY pr.nombre ASC;"
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sqlObtProveedores)
    proveedores = cursor.fetchall()
    conn.commit()
    return render_template('insumos/create.html', nombresGenericos = nombresGenericos, formasFarmaceuticas = formasFarmaceuticas, concentraciones = concentraciones, presentaciones = presentaciones, proveedores = proveedores)

@app.route('/create_publicacion')
def create_publicacion():    
    sql = "SELECT i.id as id_insumo, CONCAT_WS(' || ', i.nombre_comercial, f.nombre, c.nombre, p.nombre) as insumo FROM insumo i INNER JOIN forma_farmaceutica f ON f.id = i.id_forma_farmaceutica INNER JOIN concentracion c ON c.id = i.id_concentracion INNER JOIN proveedor p ON p.id = i.id_proveedor WHERE i.activo = 1 ORDER BY i.nombre_comercial ASC"
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sql)
    insumos = cursor.fetchall()
    conn.commit()
    sqlLugares = "SELECT l.id as id_lugar, l.nombre as lugar FROM lugar l ORDER BY l.nombre ASC"
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sqlLugares)
    lugares = cursor.fetchall()
    sqlDirecciones = "SELECT d.id as id_direccion, d.nombre as direccion FROM direccion d ORDER BY d.nombre ASC"
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sqlDirecciones)
    direcciones = cursor.fetchall()
    return render_template('publicaciones/create.html', insumos = insumos, lugares = lugares, direcciones = direcciones)

@app.route('/store_publicacion', methods=['POST'])
def storage_publicacion():
    _idInsumo = request.form['cbInsumo']    
    #_direccionEscrito = request.form['direccionPropio']    
    _direccionEscrito = request.form.get('direccionPropio')    
    if(_direccionEscrito == 'escrito'):
        _direccion = request.form['txtDirEscrito']
        #primero veo si ya esta insertado, si esta solo tomo ese id
        sqlExisteDir = "SELECT d.id FROM direccion d WHERE d.nombre = %s;"
        datosExisteDir = (_direccion)
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sqlExisteDir, datosExisteDir)
        conn.commit()
        existeDir = cursor.fetchall()
        if len(existeDir) > 0:
            lastDirId = existeDir[0][0]
        else:
            sqlDir = "INSERT INTO direccion (id, nombre) VALUES (NULL, %s);"
            datosDir = (_direccion)
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute(sqlDir, datosDir)
            conn.commit()
            lastDirId = cursor.lastrowid
    else:
        lastDirId = request.form['cbDirListado']
    #_lugarEscrito = request.form['lugarPropio']
    _lugarEscrito = request.form.get('lugarPropio')
    #poner validacion si no selecciona ningun radio checkbox
    if(_lugarEscrito == 'escrito'):
        _lugar = request.form['txtLugar']
        #primero veo si ya esta insertado, si esta solo tomo ese id
        sqlExisteLugar = "SELECT l.id FROM lugar l WHERE l.nombre = %s;"
        datosExisteLugar = (_lugar)
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sqlExisteLugar, datosExisteLugar)
        conn.commit()
        existeLugar = cursor.fetchall()
        if len(existeDir) > 0:
            lastLugarId = existeLugar[0][0]
        else:
            sqlLugar = "INSERT INTO lugar (id, nombre) VALUES (NULL, %s);"
            datosLugar = (_lugar)
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute(sqlLugar, datosLugar)
            conn.commit()
            lastLugarId = cursor.lastrowid
    else:
        lastLugarId = request.form['cbLugar']
    _precio = request.form['txtPrecio']
    _foto = request.files['txtFoto']
    #aqui validar entradas y poner mensajes de error
    if _idInsumo == '-1' or _precio == '':
        flash('Debe seleccionar un insumo')
        return redirect(url_for('create_publicacion'))
    _now = datetime.now()
    tiempo = _now.strftime("%Y%H%M%S")
    #foto validada
    nuevoNombreFoto = ''
    if _foto.filename != '':
        nuevoNombreFoto = tiempo + _foto.filename
        _foto.save("uploads/" + nuevoNombreFoto)  
    #ver si ya esta registrado, si ya esta aumentar solamente la frecuencia, si no, solo insertar
    sqlExistePub = "SELECT p.id, p.frecuencia, DATE(p.fecha_hora_creacion) AS fecha, TIME(p.fecha_hora_creacion) AS hora FROM publicacion p WHERE p.id_insumo = %s AND p.id_lugar = %s AND p.id_direccion = %s AND p.precio = %s AND p.activo = 1"
    datosExistePub = (_idInsumo, lastLugarId, lastDirId, _precio)
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sqlExistePub, datosExistePub)
    conn.commit()
    existePub = cursor.fetchall()
    if len(existePub) > 0:
        #si existe solo aumentar la frecuencia
        publicacionId = int(existePub[0][0])
        frecuencia = int(existePub[0][1])
        fechaString = existePub[0][2]
        horaString = existePub[0][3]
        frecuencia = frecuencia + 1
        #luego aplicaremos restricciones para la frecuencia        
        sql = "UPDATE publicacion p SET p.frecuencia = %s WHERE p.id = %s;"
        datos = (frecuencia, publicacionId)
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sql, datos)         
        conn.commit()
        #Luego de actualizar si hay respaldo inserto
        if len(nuevoNombreFoto) > 0:
            sqlRespaldo = "INSERT INTO respaldo (id, id_publicacion, archivo) VALUES (NULL, %s, %s);"
            datosRespaldo = (publicacionId, nuevoNombreFoto)
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute(sqlRespaldo, datosRespaldo)
            conn.commit() 
    else:
        #por ahora estamos guardando con procesado = 1 y valido = 1
        sql = "INSERT INTO publicacion (id, id_insumo, id_lugar, id_direccion, precio, procesado, valido, peso_precio, fecha_hora_creacion, activo) VALUES (NULL, %s, %s, %s, %s, '1', '1', '0', CURRENT_TIMESTAMP(), '1');"
        datos = (_idInsumo, lastLugarId, lastDirId, _precio)
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sql, datos)
        conn.commit()
        lastPublicacionId = cursor.lastrowid        
        #Inserto la publicacion primero y luego el respaldo
        if len(nuevoNombreFoto) > 0:
            sqlRespaldo = "INSERT INTO respaldo (id, id_publicacion, archivo) VALUES (NULL, %s, %s);"
            datosRespaldo = (lastPublicacionId, nuevoNombreFoto)
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute(sqlRespaldo, datosRespaldo)
            conn.commit()
        #calculo y actualizacion del peso
        #primero buscamos los valores de los precios del insumo
        sql = "SELECT i.precio_unit_max_lab, i.precio_max_venta_distr, i.precio_unit_max_priv FROM insumo i WHERE i.activo = 1 and i.id = %s"
        datos = (_idInsumo)
        conn = mysql.connect()
        cursor = conn.cursor()    
        cursor.execute(sql, datos)
        precios = cursor.fetchall()
        conn.commit()
        precio_unit_max_lab = float(precios[0][0])
        precio_max_venta_distr = float(precios[0][1])
        precio_unit_max_priv = float(precios[0][2])
        precioPublicacion = float(_precio)
        #luego actualizamos el peso precio en la publicacion
        if(precioPublicacion >= precio_max_venta_distr or precioPublicacion <= (precio_unit_max_priv * 2)):
            if (precioPublicacion > precio_unit_max_priv):            
                    valor100 = (precio_unit_max_priv * 2) - (precio_unit_max_priv + 0.1)
                    valorCalc1 = (precio_unit_max_priv * 2) - precioPublicacion
                    valorCalc2 = valor100 - valorCalc1
                    #aplico regla de tres
                    valorCalc3 = (valorCalc2 * 100) / valor100
                    #volcamos
                    peso_precio = 100 - valorCalc3
            elif (precioPublicacion < precio_unit_max_priv):
                #doy un -0.1 extra pa abarcar el precio minimo
                valor100 = precio_unit_max_priv - (precio_max_venta_distr - 0.1)
                valorCalc1 = precio_unit_max_priv - precioPublicacion
                valorCalc2 = valor100 - valorCalc1
                #aplico regla de tres
                peso_precio = (valorCalc2 * 100) / valor100
            else:
                peso_precio = 100
        sql = "UPDATE publicacion p SET p.peso_precio = %s WHERE p.id = %s;"
        datos = (peso_precio, lastPublicacionId)
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sql, datos)
        precios = cursor.fetchall()   
        conn.commit()          
        #poner mensaje de exito de proceso
    return redirect('/publicaciones')

@app.route('/store_insumo', methods=['POST'])
def storage_insumo():    
    _idNombreGenerico = request.form['cbNombreGen']
    _nombreComercial = request.form['txtNombreCom']
    _idFormaFarmaceutica = request.form['cbFormaFarm']
    _idConcentracion = request.form['cbConcentracion']
    _idPresentacion = request.form['cbPresentacion']
    _idProveedor = request.form['cbProveedor']
    _precioUnitMaxLab = request.form['txtPrecUnitMaxLab']
    _precioMaxDistrib = request.form['txtPrecMaxVentaDistrib']
    _precioUnitMaxPriv = request.form['txtPrecUnitMaxPriv']
    #if _id_insumo == '-1':
    #    flash('Debe seleccionar un insumo')
    #    return redirect(url_for('create'))    
    #_now = datetime.now()    
    sql = "INSERT INTO insumo (id, nombre_comercial, id_nombre_generico, id_forma_farmaceutica, id_concentracion, id_presentacion, id_proveedor, precio_unit_max_lab, precio_max_venta_distr, precio_unit_max_priv, fecha_hora_creacion, activo) VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP(), '1');"
    datos = (_nombreComercial, _idNombreGenerico, _idFormaFarmaceutica, _idConcentracion, _idPresentacion, _idProveedor, _precioUnitMaxLab, _precioMaxDistrib, _precioUnitMaxPriv)
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sql, datos)
    conn.commit()
    return redirect('/insumos')

if __name__== '__main__':
    app.run(debug=True)