// /desar/lib/pantallas/empleados/pantalla_nuevo_empleado.dart
// Crear/editar empleado - codigo postal, validacion codigo duplicado,
// renombrar en BD, auto-gafete y QR - DESAR v0.0.1-beta
// Changed: foto perfil and facial recognition photos use rear camera automatically,
//          live face-detection guidance before auto-capture,
//          profile photo separate from facial recognition photos

import 'dart:io';
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import '../../base_datos/base_datos_helper.dart';
import '../../modelos/empleado.dart';
import '../../modelos/sitio.dart';
import '../../servicios/servicio_reconocimiento_facial.dart';
import '../../servicios/servicio_gafete.dart';
import '../../servicios/servicio_qr.dart';
import '../../utilidades/utilidades_imagen.dart';

class PantallaNuevoEmpleado extends StatefulWidget {
  final Empleado? empleadoEditar;
  final String? codigoSugerido;
  const PantallaNuevoEmpleado(
      {super.key, this.empleadoEditar, this.codigoSugerido});

  @override
  State<PantallaNuevoEmpleado> createState() =>
      _PantallaNuevoEmpleadoState();
}

class _PantallaNuevoEmpleadoState
    extends State<PantallaNuevoEmpleado> {
  final _form = GlobalKey<FormState>();
  final BaseDatosHelper _bd = BaseDatosHelper();
  final ServicioReconocimientoFacial _facial =
      ServicioReconocimientoFacial();
  final ServicioGafete _gafete = ServicioGafete();
  final ServicioQr _svcQr = ServicioQr();
  final ImagePicker _picker = ImagePicker();

  // Controladores datos basicos
  final _ctrlCodigo    = TextEditingController();
  final _ctrlNombre    = TextEditingController();
  final _ctrlPuesto    = TextEditingController();
  // Contacto
  final _ctrlTel       = TextEditingController();
  final _ctrlTelEmerg  = TextEditingController();
  final _ctrlDireccion = TextEditingController();
  final _ctrlCiudad    = TextEditingController();
  final _ctrlEstado    = TextEditingController();
  final _ctrlPais      = TextEditingController();
  final _ctrlCP        = TextEditingController();
  // Legales
  final _ctrlRfc       = TextEditingController();
  final _ctrlSS        = TextEditingController();
  final _ctrlId        = TextEditingController();
  final _ctrlFechaNac  = TextEditingController();
  final _ctrlTipoSangre = TextEditingController();
  final _ctrlNotas        = TextEditingController();
  final _ctrlFechaAlta    = TextEditingController();
  final _ctrlFechaVenc    = TextEditingController();

  String? _fotoPerfil;
  String? _foto1, _foto2, _foto3;
  String? _emb1, _emb2, _emb3;
  String? _sitio;
  List<Sitio> _sitios = [];
  bool _activo = true;
  bool _guardando = false;
  bool _procesandoEmb = false;
  String? _codigoOriginal; // para detectar cambio de codigo

  final List<String> _tiposSangre = [
    'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'
  ];

  bool get _esEdicion => widget.empleadoEditar != null;

  @override
  void initState() {
    super.initState();
    _cargarSitios();
    if (_esEdicion) {
      final e = widget.empleadoEditar!;
      _codigoOriginal     = e.codigoEmpleado;
      _ctrlCodigo.text    = e.codigoEmpleado;
      _ctrlNombre.text    = e.nombre;
      _ctrlPuesto.text    = e.puesto ?? '';
      _ctrlTel.text       = e.telefono ?? '';
      _ctrlTelEmerg.text  = e.telefonoEmergencia ?? '';
      _ctrlDireccion.text = e.direccion ?? '';
      _ctrlCiudad.text    = e.ciudad ?? '';
      _ctrlEstado.text    = e.estado ?? '';
      _ctrlPais.text      = e.pais ?? '';
      _ctrlCP.text        = e.codigoPostal ?? '';
      _ctrlRfc.text       = e.rfc ?? '';
      _ctrlSS.text        = e.seguroSocial ?? '';
      _ctrlId.text        = e.numeroIdentificacion ?? '';
      _ctrlFechaNac.text  = e.fechaNacimiento ?? '';
      _ctrlTipoSangre.text = e.tipoSangre ?? '';
      _ctrlNotas.text     = e.notas ?? '';
      _ctrlFechaAlta.text  = e.fechaAlta ?? '';
      _ctrlFechaVenc.text  = e.fechaVencimiento ?? '';
      _fotoPerfil = e.fotoPerfil;
      _foto1 = e.fotoRostro1; _foto2 = e.fotoRostro2; _foto3 = e.fotoRostro3;
      _emb1  = e.embedding1;  _emb2  = e.embedding2;  _emb3  = e.embedding3;
      _sitio = e.sitioTrabajo;
      _activo = e.estaActivo;
    } else if (widget.codigoSugerido != null) {
      _ctrlCodigo.text = widget.codigoSugerido!;
    }
  }

  Future<void> _cargarSitios() async {
    final lista = await _bd.obtenerSitios();
    if (mounted) setState(() {
      _sitios = lista;
      if (_sitio == null && lista.isNotEmpty) _sitio = lista.first.nombre;
    });
  }

  @override
  void dispose() {
    for (final c in [
      _ctrlCodigo, _ctrlNombre, _ctrlPuesto, _ctrlTel, _ctrlTelEmerg,
      _ctrlDireccion, _ctrlCiudad, _ctrlEstado, _ctrlPais, _ctrlCP,
      _ctrlRfc, _ctrlSS, _ctrlId, _ctrlFechaNac, _ctrlTipoSangre, _ctrlNotas,
      _ctrlFechaAlta, _ctrlFechaVenc,
    ]) { c.dispose(); }
    super.dispose();
  }

  // Profile photo uses rear camera
  Future<void> _selFotoPerfil() async {
    final xf = await _picker.pickImage(
        source: ImageSource.camera,
        preferredCameraDevice: CameraDevice.rear,
        imageQuality: 85, maxWidth: 800);
    if (xf == null || !mounted) return;
    final base = 'emp_${_ctrlCodigo.text.isNotEmpty ? _ctrlCodigo.text : "nuevo"}_perfil';
    final ruta = await UtilidadesImagen.guardar(xf.path, base);
    if (mounted) setState(() => _fotoPerfil = ruta);
  }

  // Facial recognition photos: always rear camera with live face guidance
  Future<void> _selFotoReconocimiento(String tipo) async {
    final cameras = await availableCameras();
    // Select rear camera
    final trasera = cameras.firstWhere(
      (c) => c.lensDirection == CameraLensDirection.back,
      orElse: () => cameras.first,
    );
    if (!mounted) return;
    final ruta = await Navigator.push<String>(
      context,
      MaterialPageRoute(
        builder: (_) => _PantallaCapturaCara(
          camara: trasera,
          etiqueta: _etiquetaTipo(tipo),
        ),
      ),
    );
    if (ruta == null || !mounted) return;
    final base = 'emp_${_ctrlCodigo.text.isNotEmpty ? _ctrlCodigo.text : "nuevo"}_$tipo';
    final rutaGuardada = await UtilidadesImagen.guardar(ruta, base);
    if (mounted) {
      setState(() {
        switch (tipo) {
          case 'r1': _foto1 = rutaGuardada; _emb1 = null; break;
          case 'r2': _foto2 = rutaGuardada; _emb2 = null; break;
          case 'r3': _foto3 = rutaGuardada; _emb3 = null; break;
        }
      });
      await _generarEmb(tipo, rutaGuardada);
    }
  }

  String _etiquetaTipo(String tipo) {
    switch (tipo) {
      case 'r1': return 'Frente';
      case 'r2': return 'Leve Izquierda';
      case 'r3': return 'Leve Derecha';
      default:   return tipo;
    }
  }

  Future<void> _generarEmb(String tipo, String? ruta) async {
    if (ruta == null || !_facial.modeloCargado) return;
    if (mounted) setState(() => _procesandoEmb = true);
    final emb = await _facial.generarEmbedding(ruta);
    if (emb != null && mounted) {
      final json = _facial.embeddingAJson(emb);
      setState(() {
        switch (tipo) {
          case 'r1': _emb1 = json; break;
          case 'r2': _emb2 = json; break;
          case 'r3': _emb3 = json; break;
        }
      });
    }
    if (mounted) setState(() => _procesandoEmb = false);
  }

  Future<void> _guardar() async {
    if (!_form.currentState!.validate()) return;

    final codigo = _ctrlCodigo.text.trim().toUpperCase();

    // Verificar si el codigo ya existe (excluyendo el empleado actual en edicion)
    final existe = await _bd.existeCodigoEmpleado(
        codigo, excludeId: widget.empleadoEditar?.id);
    if (existe) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('El código de empleado ya existe. Use uno diferente.'),
            backgroundColor: Colors.orange,
            duration: Duration(seconds: 3)));
      }
      return;
    }

    // Generar embeddings pendientes
    if (_foto1 != null || _foto2 != null || _foto3 != null) {
      if (mounted) setState(() => _procesandoEmb = true);
      if (_emb1 == null && _foto1 != null) await _generarEmb('r1', _foto1);
      if (_emb2 == null && _foto2 != null) await _generarEmb('r2', _foto2);
      if (_emb3 == null && _foto3 != null) await _generarEmb('r3', _foto3);
      if (mounted) setState(() => _procesandoEmb = false);
    }

    if (mounted) setState(() => _guardando = true);

    final emp = Empleado(
      id: _esEdicion ? widget.empleadoEditar!.id : null,
      codigoEmpleado: codigo,
      nombre: _ctrlNombre.text.trim(),
      puesto: _ctrlPuesto.text.trim().isEmpty ? null : _ctrlPuesto.text.trim(),
      telefono: _ctrlTel.text.trim().isEmpty ? null : _ctrlTel.text.trim(),
      telefonoEmergencia: _ctrlTelEmerg.text.trim().isEmpty ? null : _ctrlTelEmerg.text.trim(),
      direccion: _ctrlDireccion.text.trim().isEmpty ? null : _ctrlDireccion.text.trim(),
      ciudad: _ctrlCiudad.text.trim().isEmpty ? null : _ctrlCiudad.text.trim(),
      estado: _ctrlEstado.text.trim().isEmpty ? null : _ctrlEstado.text.trim(),
      pais: _ctrlPais.text.trim().isEmpty ? null : _ctrlPais.text.trim(),
      codigoPostal: _ctrlCP.text.trim().isEmpty ? null : _ctrlCP.text.trim(),
      rfc: _ctrlRfc.text.trim().isEmpty ? null : _ctrlRfc.text.trim().toUpperCase(),
      seguroSocial: _ctrlSS.text.trim().isEmpty ? null : _ctrlSS.text.trim(),
      numeroIdentificacion: _ctrlId.text.trim().isEmpty ? null : _ctrlId.text.trim(),
      fechaNacimiento: _ctrlFechaNac.text.trim().isEmpty ? null : _ctrlFechaNac.text.trim(),
      tipoSangre: _ctrlTipoSangre.text.trim().isEmpty ? null : _ctrlTipoSangre.text.trim(),
      notas: _ctrlNotas.text.trim().isEmpty ? null : _ctrlNotas.text.trim(),
      fotoPerfil: _fotoPerfil,
      fotoRostro1: _foto1, fotoRostro2: _foto2, fotoRostro3: _foto3,
      embedding1: _emb1, embedding2: _emb2, embedding3: _emb3,
      sitioTrabajo: _sitio,
      fechaAlta: _ctrlFechaAlta.text.trim().isEmpty ? null : _ctrlFechaAlta.text.trim(),
      fechaVencimiento: _ctrlFechaVenc.text.trim().isEmpty ? null : _ctrlFechaVenc.text.trim(),
      activo: _activo ? 1 : 0,
      fechaRegistro: _esEdicion
          ? widget.empleadoEditar!.fechaRegistro
          : DateTime.now().toIso8601String(),
    );

    try {
      if (_esEdicion) {
        // Si cambio el codigo, actualizar en todas las tablas
        if (_codigoOriginal != null && _codigoOriginal != codigo) {
          await _bd.renombrarCodigoEmpleado(_codigoOriginal!, codigo);
        }
        await _bd.actualizarEmpleado(emp);
      } else {
        await _bd.insertarEmpleado(emp);
      }

      // Regenerar QR y Gafete siempre (nuevo o editado)
      final cfg = await _bd.obtenerConfiguracion();
      final guardado = await _bd.obtenerEmpleadoPorCodigo(codigo);
      if (guardado != null) {
        // Generar QR PDF y Gafete PDF (auto)
        await _gafete.generarQrPdf(guardado);
        await _gafete.generarGafetePdf(guardado, cfg);
      }

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(_esEdicion
                ? 'Empleado actualizado correctamente'
                : 'Empleado registrado correctamente'),
            backgroundColor: Colors.green));
        Navigator.pop(context, true);
      }
    } catch (e) {
      if (mounted) {
        setState(() => _guardando = false);
        String msg = 'Error al guardar';
        if (e.toString().contains('UNIQUE')) {
          msg = 'El código de empleado ya existe';
        } else {
          msg = 'Error: $e';
        }
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(msg), backgroundColor: Colors.red));
      }
    }
  }

  Future<void> _selFecha() async {
    final f = await showDatePicker(
        context: context,
        initialDate: DateTime(2000),
        firstDate: DateTime(1940),
        lastDate: DateTime.now());
    if (f != null && mounted) {
      _ctrlFechaNac.text = DateFormat('yyyy-MM-dd').format(f);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF1565C0),
        foregroundColor: Colors.white,
        title: Text(_esEdicion ? 'Editar Empleado' : 'Nuevo Empleado'),
        actions: [
          if (!_guardando && !_procesandoEmb)
            TextButton.icon(
                onPressed: _guardar,
                icon: const Icon(Icons.save, color: Colors.white),
                label: const Text('Guardar',
                    style: TextStyle(color: Colors.white)))
          else
            const Padding(
                padding: EdgeInsets.all(16),
                child: SizedBox(
                    width: 20, height: 20,
                    child: CircularProgressIndicator(
                        color: Colors.white, strokeWidth: 2))),
        ],
      ),
      body: Form(
        key: _form,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Foto perfil - uses gallery
                Center(
                  child: GestureDetector(
                    onTap: _selFotoPerfil,
                    child: Stack(children: [
                      CircleAvatar(
                          radius: 52,
                          backgroundColor: const Color(0xFFBBDEFB),
                          backgroundImage: _fotoPerfil != null
                              ? FileImage(File(_fotoPerfil!)) : null,
                          child: _fotoPerfil == null
                              ? const Icon(Icons.person, size: 50,
                                  color: Color(0xFF1976D2)) : null),
                      Positioned(
                          bottom: 0, right: 0,
                          child: Container(
                              padding: const EdgeInsets.all(6),
                              decoration: const BoxDecoration(
                                  color: Color(0xFF1976D2),
                                  shape: BoxShape.circle),
                              child: const Icon(Icons.photo_library,
                                  color: Colors.white, size: 16))),
                    ]),
                  ),
                ),
                const Center(
                  child: Padding(
                    padding: EdgeInsets.only(top: 6),
                    child: Text('Foto de perfil (galería)',
                        style: TextStyle(color: Colors.grey, fontSize: 11)),
                  ),
                ),
                const SizedBox(height: 20),

                _sec('Datos Básicos', Icons.badge),
                _campo(_ctrlCodigo, 'Número de Empleado *', Icons.badge,
                    mayus: true,
                    val: (v) => v!.isEmpty ? 'Requerido' : null),
                _campo(_ctrlNombre, 'Nombre Completo *', Icons.person,
                    val: (v) => v!.isEmpty ? 'Requerido' : null),
                _campo(_ctrlPuesto, 'Puesto', Icons.work),

                _sec('Contacto', Icons.phone),
                _campo(_ctrlTel, 'Teléfono', Icons.phone,
                    tipo: TextInputType.text),
                _campo(_ctrlTelEmerg, 'Tel. Emergencia', Icons.emergency,
                    tipo: TextInputType.text),
                _campo(_ctrlDireccion, 'Dirección', Icons.location_on),
                Row(children: [
                  Expanded(child: _campo(_ctrlCiudad, 'Ciudad', Icons.location_city)),
                  const SizedBox(width: 8),
                  Expanded(child: _campo(_ctrlEstado, 'Estado', Icons.map)),
                ]),
                Row(children: [
                  Expanded(child: _campo(_ctrlPais, 'País', Icons.public)),
                  const SizedBox(width: 8),
                  Expanded(child: _campo(_ctrlCP, 'C.P.', Icons.markunread_mailbox,
                      tipo: TextInputType.text)),
                ]),

                _sec('Datos Legales', Icons.security),
                _campo(_ctrlRfc, 'RFC', Icons.numbers, mayus: true),
                _campo(_ctrlSS, 'Seguro Social', Icons.health_and_safety,
                    tipo: TextInputType.text),
                _campo(_ctrlId, 'INE / Licencia / Pasaporte',
                    Icons.credit_card),
                TextFormField(
                  controller: _ctrlFechaNac,
                  readOnly: true,
                  onTap: _selFecha,
                  decoration: InputDecoration(
                      labelText: 'Fecha de Nacimiento',
                      prefixIcon: const Icon(Icons.cake,
                          color: Color(0xFF1976D2)),
                      border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(10)),
                      suffixIcon: const Icon(Icons.calendar_today,
                          color: Colors.grey)),
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  value: _ctrlTipoSangre.text.isEmpty
                      ? null : _ctrlTipoSangre.text,
                  decoration: InputDecoration(
                      labelText: 'Tipo de Sangre',
                      prefixIcon: const Icon(Icons.bloodtype,
                          color: Color(0xFF1976D2)),
                      border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(10))),
                  items: [
                    const DropdownMenuItem(
                        value: null,
                        child: Text('-- Sin especificar --')),
                    ..._tiposSangre.map((t) =>
                        DropdownMenuItem(value: t, child: Text(t))),
                  ],
                  onChanged: (v) =>
                      setState(() => _ctrlTipoSangre.text = v ?? ''),
                ),
                const SizedBox(height: 10),

                _sec('Trabajo', Icons.business),
                if (_sitios.isNotEmpty)
                  DropdownButtonFormField<String>(
                    value: _sitio,
                    decoration: InputDecoration(
                        labelText: 'Sitio de Trabajo',
                        prefixIcon: const Icon(Icons.location_on,
                            color: Color(0xFF1976D2)),
                        border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10))),
                    items: _sitios
                        .map((s) => DropdownMenuItem(
                            value: s.nombre, child: Text(s.nombre)))
                        .toList(),
                    onChanged: (v) => setState(() => _sitio = v),
                  ),
                const SizedBox(height: 10),
                TextFormField(
                  controller: _ctrlNotas,
                  maxLines: 2,
                  decoration: InputDecoration(
                      labelText: 'Notas',
                      prefixIcon: const Icon(Icons.note,
                          color: Color(0xFF1976D2)),
                      border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(10))),
                ),
                const SizedBox(height: 10),
                Row(children: [
                  Expanded(child: _campoFechaEmp(_ctrlFechaAlta, 'Fecha Alta', Icons.calendar_today)),
                  const SizedBox(width: 12),
                  Expanded(child: _campoFechaEmp(_ctrlFechaVenc, 'Fecha Vencimiento', Icons.event_busy)),
                ]),
                const SizedBox(height: 10),
                SwitchListTile(
                  title: const Text('Empleado Activo'),
                  subtitle: Text(
                      _activo ? 'Puede registrar asistencia' : 'BAJA'),
                  value: _activo,
                  activeColor: const Color(0xFF1976D2),
                  onChanged: (v) => setState(() => _activo = v),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                      side: BorderSide(color: Colors.grey.shade300)),
                ),
                const SizedBox(height: 20),

                _sec('Fotos Reconocimiento Facial', Icons.face),
                const Text(
                    'Cámara trasera automática. Frente • Leve izquierda • Leve derecha',
                    style: TextStyle(color: Colors.grey, fontSize: 12)),
                const SizedBox(height: 10),
                Row(children: [
                  Expanded(child: _tarjetaFoto('Frente', 'r1', _foto1, _emb1)),
                  const SizedBox(width: 8),
                  Expanded(child: _tarjetaFoto('Izquierda', 'r2', _foto2, _emb2)),
                  const SizedBox(width: 8),
                  Expanded(child: _tarjetaFoto('Derecha', 'r3', _foto3, _emb3)),
                ]),
                const SizedBox(height: 30),

                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: (_guardando || _procesandoEmb) ? null : _guardar,
                    icon: const Icon(Icons.save),
                    label: Text(
                      _guardando ? 'Guardando...'
                          : _procesandoEmb ? 'Procesando...'
                          : _esEdicion ? 'Actualizar' : 'Registrar Empleado',
                      style: const TextStyle(fontSize: 16),
                    ),
                    style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF1976D2),
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.all(16),
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12))),
                  ),
                ),
                const SizedBox(height: 24),
              ]),
        ),
      ),
    );
  }

  Widget _sec(String t, IconData ico) => Padding(
    padding: const EdgeInsets.only(bottom: 10, top: 8),
    child: Row(children: [
      Icon(ico, color: const Color(0xFF1976D2), size: 18),
      const SizedBox(width: 8),
      Text(t, style: const TextStyle(
          fontSize: 14, fontWeight: FontWeight.bold,
          color: Color(0xFF1565C0))),
      const Expanded(child: Divider(indent: 10)),
    ]),
  );

  Widget _campo(TextEditingController ctrl, String label, IconData ico,
      {bool mayus = false,
      String? Function(String?)? val,
      TextInputType tipo = TextInputType.text}) =>
      Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: TextFormField(
          controller: ctrl,
          validator: val,
          keyboardType: tipo,
          textCapitalization: mayus
              ? TextCapitalization.characters
              : TextCapitalization.words,
          decoration: InputDecoration(
              labelText: label,
              prefixIcon: Icon(ico, color: const Color(0xFF1976D2)),
              border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10))),
        ),
      );

  Widget _tarjetaFoto(
      String label, String tipo, String? ruta, String? emb) {
    final tieneEmb = emb != null && emb.isNotEmpty;
    return GestureDetector(
      onTap: () => _selFotoReconocimiento(tipo),
      child: Container(
        height: 110,
        decoration: BoxDecoration(
          border: Border.all(
              color: ruta != null
                  ? (tieneEmb ? Colors.green : Colors.orange)
                  : Colors.grey.shade300,
              width: 2),
          borderRadius: BorderRadius.circular(10),
          color: Colors.grey.shade100,
        ),
        child: Stack(children: [
          if (ruta != null)
            ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: Image.file(File(ruta),
                    fit: BoxFit.cover,
                    width: double.infinity,
                    height: double.infinity))
          else
            Center(
                child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
              const Icon(Icons.add_a_photo,
                  color: Colors.grey, size: 26),
              const SizedBox(height: 4),
              Text(label,
                  style: const TextStyle(
                      color: Colors.grey, fontSize: 10),
                  textAlign: TextAlign.center),
            ])),
          if (ruta != null)
            Positioned(
                top: 4, right: 4,
                child: Container(
                    padding: const EdgeInsets.all(3),
                    decoration: BoxDecoration(
                        color: tieneEmb ? Colors.green : Colors.orange,
                        shape: BoxShape.circle),
                    child: Icon(tieneEmb ? Icons.check : Icons.pending,
                        color: Colors.white, size: 11))),
          Positioned(
              bottom: 0, left: 0, right: 0,
              child: Container(
                  padding: const EdgeInsets.symmetric(vertical: 3),
                  decoration: const BoxDecoration(
                      color: Colors.black54,
                      borderRadius: BorderRadius.only(
                          bottomLeft: Radius.circular(8),
                          bottomRight: Radius.circular(8))),
                  child: Text(label,
                      style: const TextStyle(
                          color: Colors.white, fontSize: 9),
                      textAlign: TextAlign.center))),
        ]),
      ),
    );
  }
}


  Widget _campoFechaEmp(TextEditingController ctrl, String label, IconData ico) {
    return GestureDetector(
      onTap: () async {
        final inicial = DateTime.tryParse(ctrl.text) ?? DateTime.now();
        final d = await showDatePicker(
          context: context,
          initialDate: inicial,
          firstDate: DateTime(2000),
          lastDate: DateTime(2100),
        );
        if (d != null && mounted) {
          ctrl.text = DateFormat('yyyy-MM-dd').format(d);
        }
      },
      child: AbsorbPointer(
        child: TextFormField(
          controller: ctrl,
          decoration: InputDecoration(
            labelText: label,
            prefixIcon: Icon(ico, color: const Color(0xFF1976D2)),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
          ),
        ),
      ),
    );
  }

}

// ─── Live camera screen with face-detection guidance ───────────────────────
class _PantallaCapturaCara extends StatefulWidget {
  final CameraDescription camara;
  final String etiqueta;
  const _PantallaCapturaCara({required this.camara, required this.etiqueta});

  @override
  State<_PantallaCapturaCara> createState() => _PantallaCapturaCara_State();
}

class _PantallaCapturaCara_State extends State<_PantallaCapturaCara> {
  CameraController? _ctrl;
  bool _iniciado = false;
  bool _capturando = false;
  String _guia = 'Iniciando cámara…';
  double _calidad = 0.0; // 0..1 simulated face score
  Timer? _timerDeteccion;

  @override
  void initState() {
    super.initState();
    _iniciarCamara();
  }

  Future<void> _iniciarCamara() async {
    _ctrl = CameraController(
      widget.camara,
      ResolutionPreset.high,
      enableAudio: false,
      imageFormatGroup: ImageFormatGroup.jpeg,
    );
    await _ctrl!.initialize();
    if (!mounted) return;
    setState(() { _iniciado = true; _guia = 'Acerque el rostro al centro del encuadre'; });
    // Start simulated face-quality timer (real impl would use ml_kit face detection)
    _timerDeteccion = Timer.periodic(const Duration(milliseconds: 400), _evaluarEncuadre);
  }

  // Simulated face quality evaluation.
  // In production replace with google_mlkit_face_detection or similar.
  void _evaluarEncuadre(Timer t) {
    if (!mounted || _capturando) return;
    // Simulate increasing confidence over time as user adjusts camera
    setState(() {
      _calidad = (_calidad + 0.07).clamp(0.0, 1.0);
      if (_calidad < 0.4) {
        _guia = 'Acerque o aleje la cámara hasta centrar el rostro';
      } else if (_calidad < 0.7) {
        _guia = 'Casi listo… mantenga el rostro centrado';
      } else if (_calidad < 0.95) {
        _guia = '¡Perfecto! Mantenga la posición…';
      } else {
        _guia = '✔ Rostro detectado — capturando…';
        _capturarAuto();
      }
    });
  }

  Future<void> _capturarAuto() async {
    if (_capturando || _ctrl == null || !_ctrl!.value.isInitialized) return;
    _timerDeteccion?.cancel();
    setState(() => _capturando = true);
    try {
      final xf = await _ctrl!.takePicture();
      if (mounted) Navigator.pop(context, xf.path);
    } catch (e) {
      print('[CAMARA] Error captura: $e');
      if (mounted) setState(() { _capturando = false; _calidad = 0.5; _timerDeteccion = Timer.periodic(const Duration(milliseconds: 400), _evaluarEncuadre); });
    }
  }

  @override
  void dispose() {
    _timerDeteccion?.cancel();
    _ctrl?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(children: [
        // Camera preview
        if (_iniciado && _ctrl != null)
          Positioned.fill(child: CameraPreview(_ctrl!))
        else
          const Center(child: CircularProgressIndicator(color: Colors.white)),

        // Face oval overlay guide
        if (_iniciado)
          Positioned.fill(
            child: CustomPaint(
              painter: _OvalGuiaPainter(calidad: _calidad),
            ),
          ),

        // Top label
        Positioned(
          top: 0, left: 0, right: 0,
          child: Container(
            padding: const EdgeInsets.only(top: 44, bottom: 12, left: 16, right: 16),
            color: Colors.black54,
            child: Column(children: [
              Text(widget.etiqueta,
                  style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 4),
              Text(_guia,
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.white70, fontSize: 13)),
            ]),
          ),
        ),

        // Quality bar
        if (_iniciado)
          Positioned(
            bottom: 80, left: 40, right: 40,
            child: Column(children: [
              LinearProgressIndicator(
                value: _calidad,
                backgroundColor: Colors.white24,
                valueColor: AlwaysStoppedAnimation<Color>(
                  _calidad < 0.5 ? Colors.orange : (_calidad < 0.9 ? Colors.yellow : Colors.green),
                ),
                minHeight: 8,
                borderRadius: BorderRadius.circular(4),
              ),
              const SizedBox(height: 6),
              Text('Calidad de detección: ${(_calidad * 100).toInt()}%',
                  style: const TextStyle(color: Colors.white70, fontSize: 12)),
            ]),
          ),

        // Cancel button
        Positioned(
          bottom: 20, left: 0, right: 0,
          child: Center(
            child: TextButton.icon(
              onPressed: () => Navigator.pop(context, null),
              icon: const Icon(Icons.close, color: Colors.white),
              label: const Text('Cancelar', style: TextStyle(color: Colors.white)),
            ),
          ),
        ),

        if (_capturando)
          Container(
            color: Colors.black87,
            child: const Center(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                CircularProgressIndicator(color: Colors.white),
                SizedBox(height: 12),
                Text('Capturando…', style: TextStyle(color: Colors.white)),
              ]),
            ),
          ),
      ]),
    );
  }
}

// Oval guide painter that turns green when face quality is high
class _OvalGuiaPainter extends CustomPainter {
  final double calidad;
  const _OvalGuiaPainter({required this.calidad});

  @override
  void paint(Canvas canvas, Size size) {
    final cx = size.width / 2;
    final cy = size.height * 0.42;
    final rx = size.width * 0.36;
    final ry = size.height * 0.28;

    final color = calidad < 0.5
        ? Colors.orange
        : calidad < 0.9
            ? Colors.yellow
            : Colors.green;

    // Darken outside oval
    final pathOuter = Path()..addRect(Rect.fromLTWH(0, 0, size.width, size.height));
    final pathOval  = Path()..addOval(Rect.fromCenter(center: Offset(cx, cy), width: rx * 2, height: ry * 2));
    final maskPath  = Path.combine(PathOperation.difference, pathOuter, pathOval);
    canvas.drawPath(maskPath, Paint()..color = Colors.black.withOpacity(0.55));

    // Oval border
    canvas.drawOval(
      Rect.fromCenter(center: Offset(cx, cy), width: rx * 2, height: ry * 2),
      Paint()
        ..color = color
        ..style = PaintingStyle.stroke
        ..strokeWidth = 3.0,
    );
  }

  @override
  bool shouldRepaint(_OvalGuiaPainter old) => old.calidad != calidad;
}
