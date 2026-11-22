import {useId} from "react";
import MobileLogo from "../../../assets/logos/TWTDBP-Black.svg";
import {LoginImagePanel} from "./LoginImagePanel";
import {Link} from "react-router-dom";
import {ElephantLoader} from "../../animation/loader/ElephantLoader";
import {useDashboardTransition} from "../../animation/loader/useDashboardTransition";

export function LoginCard({imageSrc, signUpHref = "/signup"}) {
  const {openingDashboard, openDashboard} = useDashboardTransition();
  const id = useId();
  const usernameId = id + "-username";
  const passwordId = id + "-password";
  const titleId = id + "-title";

  function handleSubmit(event) {
    event.preventDefault();
    openDashboard();
  }

  if (openingDashboard) return <ElephantLoader />;

  return (
    <section
      aria-labelledby={titleId}
      className="mx-auto w-full max-w-md rounded-[1.75rem] bg-white text-zinc-950 shadow-xl md:grid md:max-w-5xl md:grid-cols-2 md:p-5"
    >
      <LoginImagePanel imageSrc={imageSrc} />

      <div className="flex min-w-0 items-center px-6 py-10 sm:px-10 lg:px-14">
        <div className="mx-auto w-full max-w-sm">
          <img src={MobileLogo} alt="TWTDBP" className="mb-6 w-52 md:hidden" />
          <h1 id={titleId} className="text-4xl font-semibold tracking-tight">
            Log in
          </h1>
          <p className="mt-2 text-sm text-zinc-600">
            Welcome back. Enter your details to continue
          </p>

          <form
            method="post"
            onSubmit={handleSubmit}
            className="mt-7 space-y-5 pt-4"
          >
            <div className="space-y-2">
              <label htmlFor={usernameId} className="block text-sm font-medium">
                Username or email
              </label>
              <input
                id={usernameId}
                name="username"
                type="text"
                autoComplete="username"
                autoCapitalize="none"
                spellCheck={false}
                required
                className="twtdbp-input"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor={passwordId} className="block text-sm font-medium">
                Password
              </label>
              <input
                id={passwordId}
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="twtdbp-input"
              />
            </div>

            <button
              type="submit"
              className="h-12 w-full rounded-lg bg-twtdbp-crimson px-4 font-semibold text-white hover:bg-twtdbp-crimsondark focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-twtdbp-crimson cursor-pointer"
            >
              Log in
            </button>
          </form>

          <p className="mt-4 text-center text-sm text-zinc-600">
            Do not have an account?{" "}
            <Link
              to={signUpHref}
              className="font-semibold text-twtdbp-ebony underline underline-offset-4 hover:font-bold"
            >
              Sign Up
            </Link>
          </p>
        </div>
      </div>
    </section>
  );
}
