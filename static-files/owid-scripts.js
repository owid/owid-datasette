const copyToClipboard = async (text) => {
  await navigator.clipboard.writeText(text);
};

const addCopyButtonToCell = (buttonsContainer, value) => {
  const copyButton = document.createElement("a");
  copyButton.className = "owid-button owid-copy-button fa fa-copy";
  copyButton.title = "Copy to clipboard";
  copyButton.onclick = () => copyToClipboard(value);
  buttonsContainer.append(copyButton);
};

const externalUrlFields = [
  {
    colNames: [
      "owid.charts.slug",
      "owid.slug",
      "owid.chartSlug",
      "owid.grapherSlug",
    ],
    fn: (slug) => `https://ourworldindata.org/grapher/${slug}`,
  },
  {
    colNames: ["owid.charts.id", "owid.chartId", "owid.grapherId"],
    fn: (id) => `https://owid.cloud/admin/charts/${id}/edit`,
  },
];

const externalUrlByFieldName = externalUrlFields.reduce(
  (acc, { colNames, fn }) => {
    colNames.forEach((colName) => {
      acc[colName] = fn;
    });
    return acc;
  },
  {}
);

const addExternalUrlButtonToCell = (buttonsContainer, fieldName, value) => {
  const href = externalUrlByFieldName[fieldName]?.(value);

  if (!href) return;
  const externalUrlButton = document.createElement("a");
  externalUrlButton.className =
    "owid-button owid-external-url-button fa fa-external-link-alt";
  externalUrlButton.target = "_blank";
  externalUrlButton.rel = "noopener noreferrer";
  externalUrlButton.title = "Open in new tab";
  externalUrlButton.href = href;
  buttonsContainer.appendChild(externalUrlButton);
};

const wrapInDetailsElement = (element) => {
  const detail = document.createElement("details");
  detail.className = "owid-detail";
  element.parentNode.insertBefore(detail, element);
  detail.appendChild(element);
};

let databaseName;
let tableName;
const body = document.body;
body.classList.forEach((className) => {
  if (className.startsWith("db-")) databaseName = className.replace("db-", "");
  else if (className.startsWith("table-"))
    tableName = className.replace("table-", "");
});

const cells = document.querySelectorAll("table.rows-and-columns td");
cells.forEach((cell) => {
  const value = cell.innerText;
  if (!value?.trim?.()) return;

  // Add "owid-buttons" container for any buttons
  const buttonsContainer = document.createElement("div");
  buttonsContainer.className = "owid-buttons";
  cell.appendChild(buttonsContainer);

  // Add a copy button
  addCopyButtonToCell(buttonsContainer, value);

  // Add an external URL button, linking to the grapher/admin etc.
  let colName;
  cell.classList.forEach((className) => {
    if (className.startsWith("col-")) colName = className.replace("col-", "");
  });

  const fieldName = [databaseName, tableName, colName]
    .filter((f) => f)
    .join(".");
  addExternalUrlButtonToCell(buttonsContainer, fieldName, value);

  // Wrap config JSON in a <details> tag
  if (cell.classList.contains("col-config")) {
    const pre = cell.querySelector("pre");
    if (pre) wrapInDetailsElement(pre);
  }
});
