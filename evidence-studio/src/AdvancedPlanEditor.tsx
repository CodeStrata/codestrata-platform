import Form from "@rjsf/core";
import type { RJSFSchema } from "@rjsf/utils";
import validator from "@rjsf/validator-ajv8";

type Json = Record<string, any>;

export default function AdvancedPlanEditor({ schema, plan, onChange }: { schema: RJSFSchema; plan: Json; onChange: (next: Json) => void }) {
  return <Form schema={schema} formData={plan} validator={validator} liveValidate onChange={(event) => onChange(event.formData)}><div /></Form>;
}
