(() => {
  const ui = SwaggerUIBundle({
    url: "/api/openapi.yaml",
    dom_id: "#swagger-ui",
    deepLinking: true,
    displayOperationId: true,
    docExpansion: "list",
    defaultModelsExpandDepth: 1,
    filter: true,
    tryItOutEnabled: false,
    persistAuthorization: true,
    validatorUrl: null,
    presets: [SwaggerUIBundle.presets.apis],
    layout: "BaseLayout",
  });
  window.ui = ui;
})();
