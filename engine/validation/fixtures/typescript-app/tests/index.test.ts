import app from "../src/index";

describe("health", () => {
  it("exports an express app", () => {
    expect(app).toBeDefined();
  });
});
