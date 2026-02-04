# Paso 3: Sistema de pago CON MERCADO PAGO INTEGRADO
    elif st.session_state.inscription_step == 3:
        st.markdown("#### 💳 FINALIZAR INSCRIPCIÓN")
        
        # 1. Preparar datos
        if st.session_state.inscription_type == "individual":
            count = 1
            participants = [st.session_state.current_participant]
            # Usar email del participante o uno por defecto para pruebas
            email_payer = st.session_state.current_participant.get("email", "test_user_123456@testuser.com")
            title_desc = f"Inscripción WKB: {participants[0]['nombre_completo']}"
        else:
            count = len(st.session_state.group_participants)
            participants = st.session_state.group_participants
            email_payer = participants[0].get("email", "test_user_123456@testuser.com")
            title_desc = f"Inscripción Colectiva WKB ({count} personas)"

        total_price = calculate_price(count, st.session_state.inscription_type)

        # 2. Mostrar Resumen
        st.markdown(f"""
        <div style='background: #1f2937; padding: 20px; border-radius: 10px; border-left: 5px solid #009EE3; margin-bottom: 20px;'>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h4 style='margin: 0; color: #009EE3;'>TOTAL A PAGAR</h4>
                    <small style='color: #ccc;'>Inscripción inmediata vía Mercado Pago</small>
                </div>
                <div style='font-size: 28px; font-weight: bold;'>
                    ${total_price:,.0f} CLP
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 3. Generar Link (Solo si no se ha generado ya en esta sesión para evitar duplicados)
        if 'mp_payment_link' not in st.session_state:
            with st.spinner("Conectando con Mercado Pago..."):
                link = create_mp_preference(title_desc, total_price, count, email_payer)
                st.session_state.mp_payment_link = link
        
        # 4. Interfaz de Pago
        col_pay1, col_pay2 = st.columns([1, 1], gap="large")
        
        with col_pay1:
            st.markdown("##### 1. Realizar Pago")
            st.write("Haz clic abajo para pagar de forma segura:")
            
            if st.session_state.mp_payment_link:
                # Botón oficial de Mercado Pago
                st.link_button(
                    label="PAGAR AHORA 💳", 
                    url=st.session_state.mp_payment_link, 
                    type="primary", 
                    use_container_width=True
                )
                st.caption("Se abrirá una ventana segura de Mercado Pago.")
            else:
                st.error("No se pudo generar el link de pago. Verifica tu conexión.")
        
        with col_pay2:
            st.markdown("##### 2. Confirmación Automática")
            st.info("Una vez completado el pago en la ventana emergente, haz clic en el botón de abajo para quedar inscrito inmediatamente.")
            
            # Botón para finalizar el proceso
            if st.button("✅ YA PAGUÉ: CONFIRMAR INSCRIPCIÓN", type="primary", use_container_width=True):
                
                with st.spinner("Registrando inscripción..."):
                    # Generar código único de referencia
                    payment_code = generate_payment_code()
                    st.session_state.payment_code = payment_code
                    
                    # Generar ID de grupo si aplica
                    group_id = None
                    if st.session_state.inscription_type == "colectivo":
                        group_id = 'GRP_' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    
                    saved_ids = []
                    success = True
                    
                    # Guardar cada participante con estado CONFIRMADO
                    for participant in participants:
                        # Forzamos estado "Confirmado" para inscripción inmediata
                        # Nota: En un sistema 100% automático usaríamos webhooks para validar el pago real,
                        # pero para este flujo rápido, confiamos en el click del usuario.
                        pid = save_participant(participant, st.session_state.inscription_type, group_id)
                        if pid:
                            saved_ids.append(pid)
                        else:
                            success = False
                    
                    if success and len(saved_ids) == len(participants):
                        st.session_state.inscription_step = 4
                        # Limpiar link de pago de la sesión para futura inscripción
                        del st.session_state.mp_payment_link
                        st.rerun()
                    else:
                        st.error("Hubo un error guardando los datos en la base de datos. Intenta nuevamente.")
