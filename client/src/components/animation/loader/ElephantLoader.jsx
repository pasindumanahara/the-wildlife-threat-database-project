import elephant from "../../../assets/logos/elephant-loading.svg";

export function ElephantLoader() {
  return (
    <div role="status" className="fixed inset-0 z-40 grid place-items-center bg-white">
      <img src={elephant} alt="" className="size-20" />
    </div>
  );
}
