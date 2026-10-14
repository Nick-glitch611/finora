document.addEventListener("DOMContentLoaded", () => {
    inicializarCadastro();
    inicializarLogin();
    inicializarGastos();
    inicializarConfirmacoes();
    inicializarMensagens();
});

function inicializarCadastro() {
    const formulario = document.querySelector(
        'form[action*="cadastro"]'
    );

    if (!formulario) return;

    const senha = formulario.querySelector("#senha");
    const confirmarSenha = formulario.querySelector("#confirmar_senha");
    const usuario = formulario.querySelector("#usuario");
    const email = formulario.querySelector("#email");

    formulario.addEventListener("submit", (event) => {
        if (usuario && usuario.value.trim().length < 3) {
            event.preventDefault();
            usuario.setCustomValidity(
                "O nome de usuário deve ter pelo menos 3 caracteres."
            );
            usuario.reportValidity();
            usuario.setCustomValidity("");
            return;
        }

        if (email && !email.validity.valid) {
            event.preventDefault();
            email.reportValidity();
            return;
        }

        if (senha && senha.value.length < 8) {
            event.preventDefault();
            senha.setCustomValidity(
                "A senha deve ter pelo menos 8 caracteres."
            );
            senha.reportValidity();
            senha.setCustomValidity("");
            return;
        }

        if (senha && confirmarSenha && senha.value !== confirmarSenha.value) {
            event.preventDefault();
            confirmarSenha.setCustomValidity("As senhas não coincidem.");
            confirmarSenha.reportValidity();
            confirmarSenha.setCustomValidity("");
        }
    });

    if (confirmarSenha && senha) {
        confirmarSenha.addEventListener("input", () => {
            confirmarSenha.setCustomValidity(
                confirmarSenha.value && confirmarSenha.value !== senha.value
                    ? "As senhas não coincidem."
                    : ""
            );
        });

        senha.addEventListener("input", () => {
            confirmarSenha.setCustomValidity(
                confirmarSenha.value && confirmarSenha.value !== senha.value
                    ? "As senhas não coincidem."
                    : ""
            );
        });
    }
}


function inicializarGastos() {
    const elementoDados = document.getElementById("dados-gastos");
    const canvas = document.getElementById("gastosChart");

    const formularioOrcamento = document.querySelector(
        '.form-panel form[action*="definir_orcamento"]'
    );

    const formularioGasto = document.querySelector(
        '.form-panel form[action*="adicionar_gasto"]'
    );

    if (formularioOrcamento) {
        formularioOrcamento.addEventListener("submit", (event) => {
            const campo = formularioOrcamento.querySelector(
                '[name="orcamento"]'
            );

            if (
                !campo ||
                campo.value === "" ||
                !Number.isFinite(Number(campo.value)) ||
                Number(campo.value) < 0
            ) {
                event.preventDefault();
                campo?.reportValidity();
            }
        });
    }

    if (formularioGasto) {
        formularioGasto.addEventListener("submit", (event) => {
            const descricao = formularioGasto.querySelector(
                '[name="descricao"]'
            );
            const valor = formularioGasto.querySelector('[name="valor"]');
            const categoria = formularioGasto.querySelector(
                '[name="categoria"]'
            );

            if (!descricao || !descricao.value.trim()) {
                event.preventDefault();
                descricao?.reportValidity();
                return;
            }

            if (
                !valor ||
                valor.value === "" ||
                !Number.isFinite(Number(valor.value)) ||
                Number(valor.value) <= 0
            ) {
                event.preventDefault();
                valor?.reportValidity();
                return;
            }

            if (!categoria || !categoria.value) {
                event.preventDefault();
                categoria?.reportValidity();
            }
        });
    }

    if (!canvas || !elementoDados) return;

    if (typeof Chart === "undefined") {
        console.error("Chart.js não foi carregado.");
        return;
    }

    let dados;

    try {
        dados = JSON.parse(elementoDados.textContent);
    } catch (erro) {
        console.error("Erro ao ler os dados do gráfico:", erro);
        return;
    }

    if (
        !Array.isArray(dados.categorias) ||
        !Array.isArray(dados.valores) ||
        dados.categorias.length !== dados.valores.length
    ) {
        console.error("Os dados do gráfico estão em formato inválido.");
        return;
    }

    if (dados.categorias.length === 0) return;

    if (canvas.chartInstance) {
        canvas.chartInstance.destroy();
    }

    canvas.chartInstance = new Chart(canvas, {
        type: "bar",
        data: {
            labels: dados.categorias,
            datasets: [{
                label: "Total gasto (R$)",
                data: dados.valores,
                backgroundColor: "#3978F6",
                hoverBackgroundColor: "#60A5FA",
                borderRadius: 7,
                borderSkipped: false,
                maxBarThickness: 48
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: (contexto) =>
                            "R$ " + Number(contexto.parsed.y).toLocaleString(
                                "pt-BR",
                                {
                                    minimumFractionDigits: 2,
                                    maximumFractionDigits: 2
                                }
                            )
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: "#94A3B8",
                        callback: (valor) =>
                            "R$ " + Number(valor).toLocaleString("pt-BR")
                    },
                    grid: {
                        color: "rgba(148, 163, 184, 0.15)"
                    }
                },
                x: {
                    ticks: {
                        color: "#94A3B8"
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function inicializarGastos() {
    const elementoDados = document.getElementById("dados-gastos");
    const canvas = document.getElementById("gastosChart");

    if (!elementoDados || !canvas) return;

    if (typeof Chart === "undefined") {
        console.error("Chart.js não foi carregado.");
        return;
    }

    let dados;

    try {
        dados = JSON.parse(elementoDados.textContent);
    } catch (erro) {
        console.error("Não foi possível ler os dados do gráfico.", erro);
        return;
    }

    if (
        !Array.isArray(dados.categorias) ||
        !Array.isArray(dados.valores) ||
        dados.categorias.length !== dados.valores.length
    ) {
        console.error("Os dados do gráfico estão em formato inválido.");
        return;
    }

    new Chart(canvas, {
        type: "bar",
        data: {
            labels: dados.categorias,
            datasets: [{
                label: "Total gasto (R$)",
                data: dados.valores,
                backgroundColor: "#3978F6",
                hoverBackgroundColor: "#245DCC",
                borderRadius: 7,
                borderSkipped: false,
                maxBarThickness: 48
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: (contexto) => {
                            return "R$ " + contexto.parsed.y.toLocaleString(
                                "pt-BR",
                                {
                                    minimumFractionDigits: 2,
                                    maximumFractionDigits: 2
                                }
                            );
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: (valor) => {
                            return "R$ " + Number(valor).toLocaleString("pt-BR");
                        }
                    },
                    grid: {
                        color: "#EDF1F7"
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });

    const formularioOrcamento = document.querySelector(".budget-form");

    if (formularioOrcamento) {
        formularioOrcamento.addEventListener("submit", (event) => {
            const campo = formularioOrcamento.querySelector(
                '[name="orcamento"]'
            );

            if (!campo || !campo.value || Number(campo.value) < 0) {
                event.preventDefault();
                campo?.reportValidity();
            }
        });
    }

    const formularioGasto = document.querySelector(".expense-form");

    if (formularioGasto) {
        formularioGasto.addEventListener("submit", (event) => {
            const descricao = formularioGasto.querySelector(
                '[name="descricao"]'
            );
            const valor = formularioGasto.querySelector('[name="valor"]');
            const categoria = formularioGasto.querySelector(
                '[name="categoria"]'
            );

            if (!descricao?.value.trim()) {
                event.preventDefault();
                descricao?.reportValidity();
                return;
            }

            if (
                !valor ||
                !valor.value ||
                !Number.isFinite(Number(valor.value)) ||
                Number(valor.value) <= 0
            ) {
                event.preventDefault();
                valor?.reportValidity();
                return;
            }

            if (!categoria?.value) {
                event.preventDefault();
                categoria?.reportValidity();
            }
        });
    }
}

function inicializarConfirmacoes() {
    const formularios = document.querySelectorAll(
        'form[action*="remover_gasto"]'
    );

    formularios.forEach((formulario) => {
        formulario.addEventListener("submit", (event) => {
            const confirmado = window.confirm(
                "Deseja realmente remover este gasto?"
            );

            if (!confirmado) {
                event.preventDefault();
            }
        });
    });
}

function inicializarMensagens() {
    const mensagens = document.querySelectorAll(".flash-message");

    mensagens.forEach((mensagem) => {
        mensagem.setAttribute("role", "status");

        if (
            mensagem.classList.contains("error") ||
            mensagem.classList.contains("danger")
        ) {
            mensagem.setAttribute("role", "alert");
        }
    });
}