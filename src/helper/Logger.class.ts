export default class Logger {
  public static log<T>(e: T): T | undefined {
    console.log(e);
    return e;
  }

  public static dev<T>(e: T): T | undefined {
    console.warn(e);
    return e;
  }
}
